__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "6/14/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import logging
import os
import sys
import warnings
from typing import Dict, List

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai.embeddings import OpenAIEmbeddings
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt.chat_agent_executor import create_react_agent, create_react_agent as _create_react_agent
from langgraph_supervisor import create_supervisor

from agentfoundry.agents.base_agent import BaseAgent
from agentfoundry.agents.tools.memory_tools import delete_recall_memory, save_recall_memory, search_recall_memories
from agentfoundry.llm.llm_factory import LLMFactory
from agentfoundry.registry.tool_registry import ToolRegistry
from agentfoundry.utils.config import Config
from agentfoundry.utils.logger import get_logger

# Suppress Pydantic underscore-field warnings
warnings.filterwarnings(
    "ignore",
    message="fields may not start with an underscore",
    category=RuntimeWarning,
)

micropolicy_prompt = """
You are an expert in extracting compliance rules from text and return them exclusively as a valid JSON array. 

Each JSON object in the array MUST include these keys:
- "rule": (string) A short, concise title of the compliance rule.
- "description": (string) A clear, detailed explanation of the compliance rule.
- "value": (optional string) A specific numerical value or threshold explicitly mentioned in the rule.

JSON Example:
[{
"rule": "RSA encryption key length",
"description": "Minimum acceptable RSA encryption key length",
"value": "2048"
}]

STRICT REQUIREMENTS:
- You MUST respond ONLY with a valid JSON array.
- You MUST NOT include any summaries, commentary, explanations, or additional text outside the JSON structure.
- The description should be an actionable issue that can be used to CHECK if a rule is being enforced. For example, instead of "name a security officer", use something like "verify there is a named security officer"
"""

embedding = OpenAIEmbeddings()
# embedding = OllamaEmbeddings(model="bge-large")
faiss_index_path = Config().get("FAISS_INDEX_PATH", "./faiss_index")
if os.path.exists(faiss_index_path):
    recall_vector_store = FAISS.load_local(faiss_index_path, embedding, allow_dangerous_deserialization=True)
else:
    recall_vector_store = FAISS.from_documents(
        [Document(page_content="Initial page", metadata={"user_id": "initial"})], embedding)
    recall_vector_store.save_local(faiss_index_path)


# Create specialist agent
def make_specialist(name: str, tools: List[tool], llm, prompt:str = None) -> CompiledGraph:
    """ Create a specialist agent with the given name, tools, and LLM."""
    agent_name = " ".join(name.split("_")[:-1])
    if prompt is None:
        prompt = (
            f"You are a {agent_name} agent.\n\n"
            "INSTRUCTIONS:\n"
            f"- Assist ONLY with {agent_name}-related tasks\n"
            "- After you're done with your tasks, respond to the supervisor directly\n"
            "- Respond ONLY with the results of your work, do NOT include ANY other text."
        )
    return create_react_agent(llm, tools, prompt=prompt, name=name, checkpointer=MemorySaver())


# Orchestrator with single supervisor and any number of specialist agents
class Orchestrator(BaseAgent):
    """
    Orchestrator orchestrates multiple specialist agents and manages memory tools.
    """

    def __init__(self, tool_registry: ToolRegistry, llm = None):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Initializing Orchestrator")
        self.registry = tool_registry
        # Map agent names to tool identifiers
        agent_tool_map: Dict[str, List[str]] = dict[str, List[str]]()  # FIXME: Why was this trying to use the tool registry?
        self.logger.debug(f"Agent tool map keys: {list(agent_tool_map.keys())}")
        base_llm = llm or LLMFactory.get_llm_model()

        # Build specialists and handoff tools
        specialists = []
        for name, tools in agent_tool_map.items():
            tools += [save_recall_memory, search_recall_memories, delete_recall_memory]
            if name == "micropolicy_agent":
                specialist = make_specialist(name, tools, base_llm, prompt=micropolicy_prompt)
            else:
                specialist = make_specialist(name, tools, base_llm)
            specialists.append(specialist)
        self.logger.info(f"Built {len(specialists)} specialist agents: {list(agent_tool_map.keys())}")

        # Build supervisor using langgraph_supervisor
        prompt = (
            "You are a supervisor coordinating agents: " +
            ", ".join(agent_tool_map.keys()) +
            ". Route tasks by calling the appropriate handoff tool, or return '__end__' when done."
            "Memory Usage Guidelines:\n"
            "1. Actively use memory tools (save_core_memory, save_recall_memory) to build a comprehensive understanding of the user.\n"
            "2. Make informed suppositions and extrapolations based on stored memories.\n"
            "3. Regularly reflect on past interactions to identify patterns and preferences.\n"
            "4. Update your mental model of the user with each new piece of information.\n"
            "5. Cross-reference new information with existing memories for consistency.\n"
            "6. Prioritize storing emotional context and personal values alongside facts.\n"
            "7. Use memory to anticipate needs and tailor responses to the user's style.\n"
            "8. Recognize and acknowledge changes in the user's situation or perspectives over time.\n"
            "9. Leverage memories to provide personalized examples and analogies.\n"
            "10. Recall past challenges or successes to inform current problem-solving."
            "11. Understand that memory also has a security level. User's with lower security cannot access memories saved by users with higher security levels."
            "12. If a user asks for a new Tool or Python code, attempt to use the `python_tool_creator` tool first if possible."
            "13. If you a returning the file path to a modified file, please return it at the end of the response and encapsulated like the following example: (new_file: PATH/To/File). If there are multiple files, use"
            "multiple parentheses."
            "14. Please save the rules that are generated from the compliance agent and for any task, check if any of "
            "the saved compliance rules need to be applied. In the case of PHI, do not remove the columns, aim to de-identify or mask them."
        )
        self.logger.info("Compiling supervisor with langgraph_supervisor")
        try:
            self.supervisor = create_supervisor(
                agents=specialists,
                model=base_llm,
                prompt=prompt,
                tools=[save_recall_memory, search_recall_memories, delete_recall_memory],
                add_handoff_messages=True,
                add_handoff_back_messages=True,
                parallel_tool_calls=True,
                output_mode="full_history"
            ).compile(checkpointer=MemorySaver())
        except TypeError as e:
            self.logger.warning(
                "create_supervisor failed (unsupported args), falling back to create_react_agent: %s", e
            )
            # Fallback to basic supervisor agent (CompiledGraph returned directly)
            self.supervisor = _create_react_agent(
                model=base_llm,
                tools=[save_recall_memory, search_recall_memories, delete_recall_memory],
                prompt=prompt,
                checkpointer=MemorySaver(),
                name="supervisor",
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize supervisor: {e}", exc_info=True)
            self.supervisor = None

        if self.supervisor is None:
            raise RuntimeError("Supervisor failed to initialize; cannot run tasks")

    def run_task(self, task: str, *args, **kwargs):
        """Run a single task through the supervisor pipeline."""
        return_additional = kwargs.get('additional', False)
        config = kwargs.get('config') or {"configurable": {"user_id": "1", "thread_id": "1", "org_id": "NA", "security_level": "1"}}
        self.logger.info(f"run_task invoked: task={task}, additional={return_additional}")
        init = {"messages": [HumanMessage(content=task)]}
        if self.supervisor is None:
            raise RuntimeError("Supervisor not initialized; cannot execute task")
        try:
            responses = self.supervisor.invoke(init, config=config)
            reply = responses['messages'][-1].content
            self.logger.debug(f"Supervisor responses: {responses}")
        except Exception as e:
            self.logger.error(f"Exception in run_task for task '{task}': {e}", exc_info=True)
            raise
        if return_additional:
            return reply, responses
        self.logger.info(f"run_task completed: reply={reply}")
        return reply

    def chat(self, messages: list[dict], config: dict = None, additional: bool = False):
        """
        Multi-turn conversational interface using the supervisor pipeline.
        Args:
            messages: List of dicts with 'role' and 'content' keys representing the conversation history.
            config: Optional config dict for memory tools (user_id, thread_id, org_id, security_level).
            additional: If True, returns (response, full supervisor output).
        Returns:
            The assistant's reply, or (reply, full output) if additional=True.
        """
        self.logger.info(f"chat invoked: messages_count={len(messages)}, additional={additional}")
        if config is None:
            config = {"configurable": {"user_id": "1", "thread_id": "1", "org_id": "NA", "security_level": "1"}}
        self.logger.debug(f"chat config: {config}")
        # Convert raw messages to message objects
        msg_objs = []
        for msg in messages:
            role = msg.get("role", "").lower()
            content = msg.get("content", "")
            if role == "system":
                msg_objs.append(SystemMessage(content=content))
            elif role == "user":
                msg_objs.append(HumanMessage(content=content))
            elif role in ("assistant", "ai"):
                msg_objs.append(AIMessage(content=content))
            else:
                raise ValueError(f"Unknown message role: {role}")
        init = {"messages": msg_objs}
        responses = self.supervisor.invoke(init, config=config)
        reply = responses['messages'][-1].content
        if additional:
            self.logger.info(f"chat completed with additional output: reply={reply}")
            return reply, responses
        self.logger.info(f"chat completed: reply={reply}")
        return reply


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Set to DEBUG to capture all log levels
    # Create handler that outputs to stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    # Create a formatter and set it on the handler
    # formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s - %(name)-32s:%(lineno)-5s  - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    stdout_handler.setFormatter(formatter)
    # Add the handler to the logger
    logger.addHandler(stdout_handler)
    logging.getLogger("httpcore").setLevel(logging.WARNING)  # Suppress httpcore warnings
    logging.getLogger("openai").setLevel(logging.WARNING)  # Suppress OpenAI warnings
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    registry = ToolRegistry()
    registry_tool = registry.as_langchain_registry_tool()
    registry.register_tool(registry_tool)
    registry.load_tools_from_directory("")
    available_tools = registry.as_langchain_tools()
    tool_agent_dict = {
        "internet_request_agent": [available_tools[3], available_tools[4], available_tools[5]],
        "database_agent": [available_tools[-1]]
    }
    registry.agent_tools = tool_agent_dict
    try:
        orchestrator = Orchestrator(registry)
        cfg = {'configurable': {'user_id': 'u1', 'thread_id': 't1', 'org_id': 'o1', 'security_level': "10"}}
        response1 = orchestrator.run_task(
            "Remember that my favorite color is blue.", config=cfg
        )
        print("Task 1 Response:", response1)

        # Task 2: Recall memory
        task2 = "What is my favorite color?"
        response2 = orchestrator.run_task(task2, config=cfg)
        print("Task 2 Response:", response2)

        # Verify that the memory was recalled correctly
        assert "blue" in response2.lower(), \
            "Memory recall failed: 'blue' not found in response"
        print("Smoke test passed: Memory successfully saved and recalled.")
    except Exception as e:
        print(f"ERROR (example harness): {e}")
        sys.exit(1)
