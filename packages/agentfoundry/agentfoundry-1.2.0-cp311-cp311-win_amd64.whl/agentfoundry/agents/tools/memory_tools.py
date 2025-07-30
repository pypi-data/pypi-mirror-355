__author__ = "Chris Steel"
__copyright__ = "Copyright 2025, Syntheticore Corporation"
__credits__ = ["Chris Steel"]
__date__ = "6/14/2025"
__license__ = "Syntheticore Confidential"
__version__ = "1.0"
__email__ = "csteel@syntheticore.com"
__status__ = "Production"

import os
import uuid
from typing import List
from typing_extensions import TypedDict

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langgraph.graph import MessagesState

from agentfoundry.utils.config import Config

_embedding = OpenAIEmbeddings()
faiss_index_path = Config().get("FAISS_INDEX_PATH", "./faiss_index")
if os.path.exists(faiss_index_path):
    recall_vector_store = FAISS.load_local(
        faiss_index_path, _embedding, allow_dangerous_deserialization=True
    )
else:
    recall_vector_store = FAISS.from_documents(
        [Document(page_content="Initial page", metadata={"user_id": "initial"})],
        _embedding,
    )
    recall_vector_store.save_local(faiss_index_path)

def get_config_param(config: RunnableConfig, param_name: str) -> str:
    """
    Extract a required parameter from the agent's RunnableConfig.
    """
    value = config.get("configurable", {}).get(param_name)
    if value is None:
        raise ValueError(f"{param_name} needs to be provided to save a memory.")
    return value

class KnowledgeTriple(TypedDict):
    subject: str
    predicate: str
    object_: str


class State(MessagesState):
    # add memories that will be retrieved based on the conversation context
    recall_memories: List[str]
    summary: str
    modified_memories: str


# Explore - multi agent systems


@tool
def save_recall_memory(memories: List[KnowledgeTriple], config: RunnableConfig) -> list[KnowledgeTriple]:
    """Save memory to vectorstore for later semantic retrieval."""
    user_id = get_config_param(config, param_name="user_id")
    org_id = get_config_param(config, param_name="org_id")
    for memory in memories:
        serialized = " ".join(memory.values())
        document = Document(
            serialized,
            id=str(uuid.uuid4()),
            metadata={
                "user_id": user_id,
                "org_id": org_id,
                **memory,
            },
        )
        recall_vector_store.add_documents([document])
    recall_vector_store.save_local(faiss_index_path)
    return memories

@tool
def search_recall_memories(query: str, config: RunnableConfig) -> List[str]:
    """Search for relevant memories."""
    user_id = get_config_param(config, param_name="user_id")
    org_id = get_config_param(config, param_name="org_id")

    def _filter_function(doc: Document) -> bool:
        return doc.metadata.get("user_id", None) == user_id or doc.metadata.get("org_id", None) == org_id

    documents = recall_vector_store.similarity_search(
        query, k=3
    )
    documents = [docu for docu in documents if _filter_function(docu)]
    return [document.page_content for document in documents]


@tool
def delete_recall_memory(
    query: str, config: RunnableConfig, k: int
) -> List[Document]:
    """Function to search for and remove the top k number of docs matching the search query and returning the deleted documents"""
    user_id = get_config_param(config, param_name="user_id")
    org_id = get_config_param(config, param_name="org_id")

    def _filter_function(doc: Document) -> bool:
        return doc.metadata.get("user_id", None) == user_id or doc.metadata.get("org_id", None) == org_id

    documents = recall_vector_store.similarity_search(
        query, k=k
    )
    documents = [docu for docu in documents if _filter_function(docu)]
    if len(documents) > 0:
        docu_ids = [docu.id for docu in documents]
        _ = recall_vector_store.delete(ids=docu_ids)
    return documents