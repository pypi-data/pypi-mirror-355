import os

import tiktoken
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage, get_buffer_string
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_openai.embeddings import OpenAIEmbeddings
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from agentfoundry.agents.base_agent import BaseAgent
from agentfoundry.agents.tools.memory_tools import State, delete_recall_memory, save_recall_memory, search_recall_memories
from agentfoundry.llm.llm_factory import LLMFactory
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.utils.config import Config
from agentfoundry.utils.logger import get_logger


def pretty_print_stream_chunk(chunk):
    for node, updates in chunk.items():
        print(f"Update from node: {node}")
        if updates is None:
            print(f"No update from {node}")
        elif "messages" in updates:
            print("MESSAGE:")
            updates["messages"][-1].pretty_print()
        else:
            print("Update:", updates)
        print("\n")


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant with advanced long-term memory"
            " capabilities. Powered by a stateless LLM, you must rely on"
            " external memory to store information between conversations."
            " Utilize the available memory tools to store and retrieve"
            " important details that will help you better attend to the user's"
            " needs and understand their context.\n\n"
            "Memory Usage Guidelines:\n"
            "1. Actively use memory tools (save_core_memory, save_recall_memory)"
            " to build a comprehensive understanding of the user.\n"
            "2. Make informed suppositions and extrapolations based on stored"
            " memories.\n"
            "3. Regularly reflect on past interactions to identify patterns and"
            " preferences.\n"
            "4. Update your mental model of the user with each new piece of"
            " information.\n"
            "5. Cross-reference new information with existing memories for"
            " consistency.\n"
            "6. Prioritize storing emotional context and personal values"
            " alongside facts.\n"
            "7. Use memory to anticipate needs and tailor responses to the"
            " user's style.\n"
            "8. Recognize and acknowledge changes in the user's situation or"
            " perspectives over time.\n"
            "9. Leverage memories to provide personalized examples and"
            " analogies.\n"
            "10. Recall past challenges or successes to inform current"
            " problem-solving.\n\n"
            "## Recall Memories\n"
            "Recall memories are contextually retrieved based on the current"
            " conversation:\n{recall_memories}\n\n"
            "## Instructions\n"
            "Engage with the user naturally, as a trusted colleague or friend."
            " There's no need to explicitly mention your memory capabilities."
            " Instead, seamlessly incorporate your understanding of the user"
            " into your responses. Be attentive to subtle cues and underlying"
            " emotions. Adapt your communication style to match the user's"
            " preferences and current emotional state. Use tools to persist"
            " information you want to retain in the next conversation. If you"
            " do call tools, all text preceding the tool call is an internal"
            " message. Respond AFTER calling the tool, once you have"
            " confirmation that the tool completed successfully.\n\n",
        ),
        ("placeholder", "{messages}"),
    ]
)

embedding = OpenAIEmbeddings()
faiss_index_path = Config().get("FAISS_INDEX_PATH", "./faiss_index")
if os.path.exists(faiss_index_path):
    recall_vector_store = FAISS.load_local(faiss_index_path, embedding, allow_dangerous_deserialization=True)
else:
    recall_vector_store = FAISS.from_documents(
        [Document(page_content="Initial page", metadata={"user_id": "initial"})], embedding)
    recall_vector_store.save_local(faiss_index_path)


def get_config_param(config: RunnableConfig, param_name: str) -> str:
    param = config["configurable"].get(param_name)
    if param is None:
        raise ValueError(f"{param_name} needs to be provided to save a memory.")
    return param


class ToolAutonomyAgent(BaseAgent):

    def __init__(self, tool_registry, llm=None, tokenizer=None):
        """
        Initialize the Tool Autonomy Agent with a tool registry and an LLM instance.
        max_iterations controls the number of reactive turns.
        """
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.tool_registry = tool_registry
        self.tool_registry.load_tools_from_directory(Config().get("TOOLS_DIR", None))
        self.available_tools = self.tool_registry.as_langchain_tools()
        self.available_tools.extend([
            save_recall_memory,
            search_recall_memories,
            delete_recall_memory
        ])
        self.prompt = prompt
        if llm is None:
            self.llm = LLMFactory.get_llm_model()
        else:
            self.llm = llm
        self.model_with_tools = self.llm.bind_tools(self.available_tools)
        if tokenizer is None:
            tokenizer = tiktoken.encoding_for_model("gpt-4o")  # FIXME: Eventually move to Config file
        self.tokenizer = tokenizer

        self.builder = StateGraph(State)
        self.builder.add_node(self.load_memories)
        self.builder.add_node(self.agent)
        self.builder.add_node("tools", ToolNode(self.available_tools))
        self.builder.add_node(self.summarize_conversation)
        self.builder.add_node(self.preprocess_memories)

        # Add edges to the graph
        self.builder.add_edge(START, "load_memories")
        self.builder.add_edge("load_memories", "preprocess_memories")
        self.builder.add_edge("preprocess_memories", "agent")
        self.builder.add_conditional_edges("agent", self.route_tools, ["tools", "summarize_conversation", END])
        self.builder.add_edge("tools", "agent")
        self.builder.add_edge("summarize_conversation", END)

        # Compile the graph
        memory = MemorySaver()
        self.graph = self.builder.compile(checkpointer=memory)

    def preprocess_memories(self, state: State):
        recall_str = (
                "<recall_memory>\n" + "\n".join(state["recall_memories"]) + "\n</recall_memory>"
        )
        summary = state.get("summary", "")
        messages = state["messages"]
        prompt_string = messages[-1].content
        prompt_string += f"\n\nRecalled memories: {recall_str}\n\nSummary: {summary}\n" \
                         "Given the message requests, the recalled memories, and the summary of " \
                         "the previous messages, preprocess the memories to identify relevant " \
                         "information only into a single string. Additionally, assess whether " \
                         "more information is required to satisfy the user's request. You do not need to fact check " \
                         "the memories."
        prediction = self.llm.invoke(prompt_string)
        return {
            "modified_memories": prediction
        }

    @staticmethod
    def should_continue(state: State):
        """Return the next node to execute."""
        # messages = state["messages"]
        # If there are more than six messages, then we summarize the conversation
        # if len(messages) > 6:
        #     return "summarize_conversation"
        # Otherwise we can just end
        return END

    def summarize_conversation(self, state: State):
        # build your summary prompt
        summary = state.get("summary", "")
        if summary:
            summary_message = (
                f"This is the summary so far: {summary}\n\n"
                "Extend it by incorporating the new messages above:"
            )
        else:
            summary_message = "Create a summary of the conversation above:"

        # clean out any AIMessage.tool_calls before summarizing
        cleaned_messages = []
        for m in state["messages"]:
            # drop the *invocation* messages that still have tool_calls
            if (isinstance(m, ToolMessage)) or (isinstance(m, AIMessage) and getattr(m, "tool_calls", None)):
                continue
            # keep normal human, tool, or assistant messages
            cleaned_messages.append(m)

        # append your summary‐request as the last user message
        cleaned_messages.append(HumanMessage(content=summary_message))

        # now call the LLM with a history that has no stray tool_calls
        response = self.llm.invoke(cleaned_messages)

        # prune old messages as before
        eligible = [
            m for m in state["messages"]
            if not isinstance(m, ToolMessage)
               and not (isinstance(m, AIMessage) and getattr(m, "tool_calls", None))
        ]

        # 2) grab the last three of those
        keep = eligible[-3:]

        # 3) delete everything else
        delete_messages = [
            RemoveMessage(id=m.id)
            for m in state["messages"]
            if m not in keep
        ]
        return {
            "summary": response.content,
            "messages": delete_messages,
        }

    def agent(self, state: State):
        """Process the current state and generate a response using the LLM.

        Args:
            state (schemas.State): The current state of the conversation.

        Returns:
            schemas.State: The updated state with the agent's response.
        """
        bound = self.prompt | self.model_with_tools
        recall_str = (
                "<recall_memory>\n" + "\n".join(state["recall_memories"]) + "\n</recall_memory>"
        )
        # summary = state.get("summary", "")
        prediction = bound.invoke(
            {
                "messages": state["messages"],
                "recall_memories": recall_str,
                "summary": state["modified_memories"],
            }
        )
        return {
            "messages": [prediction],
        }

    def load_memories(self, state: State, config: RunnableConfig):
        """Load memories for the current conversation.

        Args:
            state (schemas.State): The current state of the conversation.
            config (RunnableConfig): The runtime configuration for the agent.

        Returns:
            State: The updated state with loaded memories.
        """
        convo_str = get_buffer_string(state["messages"])
        convo_str = self.tokenizer.decode(self.tokenizer.encode(convo_str)[:2048])
        recall_memories = search_recall_memories.invoke(convo_str, config)
        return {
            "recall_memories": recall_memories,
        }

    def route_tools(self, state: State):
        """Determine whether to use tools or end the conversation based on the last message.

        Args:
            state (schemas.State): The current state of the conversation.

        Returns:
            Literal["tools", "__end__"]: The next step in the graph.
        """
        msg = state["messages"][-1]
        if msg.tool_calls:
            return "tools"
        return self.should_continue(state)

    def run_task(self, task: str, *args, **kwargs):
        config = RunnableConfig(configurable={"user_id": "1", "thread_id": "1", "org_id": "igentic"})
        output = []
        for chunk in self.graph.stream({"messages": [("user", task)]}, config=config):
            pretty_print_stream_chunk(chunk)
            for node, updates in chunk.items():
                if "messages" in updates:
                    if type(updates['messages'][-1]) == AIMessage:
                        output.append(updates['messages'][-1].content)
        return "\n".join(output)

    def chat(self, messages: list[dict], config: dict = None, additional: bool = False):
        pass

if __name__ == "__main__":

    # Initialize the tool registry
    tool_registry = ToolRegistry()

    # Initialize the agent with the tool registry and an LLM instance
    llm = LLMFactory.get_llm_model()
    agent = ToolAutonomyAgent(tool_registry, llm=llm)

    # Define test parameters
    user_id = "test_user"
    org_id = "test_org"
    config = {"configurable": {"user_id": user_id, "thread_id": "test_thread", "org_id": org_id}}

    # Task 1: Save memory
    task1 = "Remember that my favorite color is blue."
    response1 = agent.run_task(task1, config=config)
    print("Task 1 Response:", response1)

    # Task 2: Recall memory
    task2 = "What is my favorite color?"
    response2 = agent.run_task(task2, config=config)
    print("Task 2 Response:", response2)

    # Verify that the memory was recalled correctly
    assert "blue" in response2.lower(), "Memory recall failed: 'blue' not found in response"
    print("Smoke test passed: Memory successfully saved and recalled.")

    # Clean up the FAISS index
    # if os.path.exists(faiss_index_path):
    #    shutil.rmtree(faiss_index_path)
    #    print(f"Cleaned up FAISS index at {faiss_index_path}")
