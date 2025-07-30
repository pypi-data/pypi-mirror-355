import uuid
from typing import Sequence

import chromadb
from chromadb.types import Collection
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

from agentfoundry.utils.config import Config
from agentfoundry.utils.logger import get_logger


class ChromadbClient:

    def __init__(self, persist_directory: str = None, collection_name: str = 'default', settings: dict = None):
        """
        Initialize the ChromaDB client with a persistent directory.

        Args:
            persist_directory (str): Directory where the ChromaDB database will be stored.
        """
        self.logger = get_logger(__name__)
        if persist_directory:
            self.persist_directory = persist_directory
        else:
            self.persist_directory = Config().get("CHROMA_PERSIST_DIRECTORY", os.path.join(Config().get("DATA_DIR"), "chromadb"))
        if not os.path.exists(self.persist_directory):
            os.makedirs(self.persist_directory)
        self.logger.info(f"Initializing ChromaDB client with persist_directory: {persist_directory}")

        if not collection_name:
            collection_name = Config().get("CHROMA_COLLECTION_NAME")
            self.logger.info(f"Using default collection name: {collection_name}")
        # Initialize the client with the given persistent directory
        self.logger.info(f"Connecting to ChromaDB at: {self.persist_directory}")
        self.client = chromadb.PersistentClient(path=self.persist_directory)

        collections = self.client.list_collections()
        for collection in collections:
            self.logger.info(f"Found ChromaDB Collection Name: {collection}")
        # self.client = chromadb.HttpClient(host="localhost", port=8000)

        # Create custom embedding function
        self.embedding_function = SentenceTransformerEmbeddingFunction(
            model_name=Config().get("EMBEDDING_MODEL_NAME"),
            use_auth_token=Config().get("HF_TOKEN")
        )
        self.logger.info(f"Using embedding model: {Config().get('EMBEDDING_MODEL_NAME')}")

        # Create or get the collection with the custom embedding function
        self.collection = self.client.get_or_create_collection(
            collection_name,
            embedding_function=self.embedding_function
        )
        self.logger.info(f"ChromaDB collection '{collection_name}' is ready with count: {self.collection.count()}")

    def store_results(self, results: list):
        """
        Store a list of results into the ChromaDB collection without duplicating existing entries.

        Each result is expected to be a dictionary containing:
          - 'id' (optional): a unique identifier for the result. If not provided, one is generated.
          - 'text': the text content to store.
          - 'embedding': a list of floats representing the vector embedding (optional).
          - 'metadata' (optional): any additional metadata as a dict.

        The method first checks for each result whether an exact text match already exists in the collection.
        If a duplicate is found, the result is skipped.

        Args:
            results (list): List of dictionaries representing individual results.
        """
        new_ids = []
        new_documents = []
        new_embeddings = []
        new_metadatas = []

        for result in results:
            text = result.get("text", "")
            if not text:
                self.logger.warning("Result missing text field; skipping.")
                continue

            # Query for an existing document with the same text.
            query_result = self.collection.query(
                query_texts=[text],
                n_results=1,
                include=['documents', 'distances']
            )
            duplicate_found = False
            documents_result = query_result.get("documents", [])
            if documents_result and len(documents_result) > 0 and len(documents_result[0]) > 0:
                candidate = documents_result[0][0]
                if candidate == text:
                    duplicate_found = True

            if duplicate_found:
                self.logger.info(f"Duplicate found for text: {text[:30]}... Skipping storing this result.")
            else:
                # Use provided id or generate one.
                item_id = result.get("id", str(uuid.uuid4()))
                new_ids.append(item_id)
                new_documents.append(text)
                new_embeddings.append(result.get("embedding", None))
                new_metadatas.append(result.get("metadata", {}))

        if new_documents:
            self.collection.add(
                ids=new_ids,
                documents=new_documents,
                embeddings=new_embeddings if any(e is not None for e in new_embeddings) else None,
                metadatas=new_metadatas
            )
            self.logger.info(f"Stored {len(new_documents)} new result(s) in the ChromaDB collection.")
        else:
            self.logger.info("No new results to store. All provided results are duplicates.")

    def query(self, query_embedding: list, n_results: int = 5):
        try:
            self.logger.info(f"Querying ChromaDB with n_results={n_results}")
            if not query_embedding or not isinstance(query_embedding, list):
                raise ValueError("query_embedding must be a non-empty list")

            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['documents', 'embeddings', 'distances', 'metadatas']
            )
            self.logger.info("Query complete.")
            return results
        except Exception as e:
            self.logger.error(f"Query failed: {str(e)}")
            raise

    def query_text(self, query_text: str, n_results: int = 5):
        """
        Query the ChromaDB collection using plain text instead of embeddings.
        """
        if not isinstance(query_text, str) or not query_text.strip():
            self.logger.error("query_text must be a non-empty string")
            raise ValueError("query_text must be a non-empty string")

        self.logger.info(f"Querying ChromaDB with text query, n_results={n_results}")
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            include=['documents', 'embeddings', 'distances', 'metadatas']
        )
        self.logger.info("Text query complete.")
        return results

    def delete_collection(self, collection_name: str) -> None:
        """
        Delete a collection from the ChromaDB database.

        Args:
            collection_name (str): The name of the collection to delete.
        """
        self.logger.info(f"Deleting collection: {collection_name}")
        try:
            self.client.delete_collection(name=collection_name)
            self.logger.info(f"Collection {collection_name} deleted successfully.")
        except ValueError as e:
            self.logger.error(f"Failed to delete collection: {e}")

    def list_collections(self) -> Sequence[Collection]:
        """
        List all collections in the ChromaDB database.

        Returns:
            list: A list of collection objects, each containing name and metadata.
        """
        self.logger.info("Listing all collections in ChromaDB")
        collections = self.client.list_collections()
        self.logger.info(f"Found {len(collections)} collections")
        return collections

    def get_or_create_collection(self, name: str, embedding_function: any = None):
        if not embedding_function:
            embedding_function = self.embedding_function
        if embedding_function != self.embedding_function:
            error_str = f"Embedding function supplied: {embedding_function} must match this client's: {self.embedding_function}"
            self.logger.error(error_str)
            # raise ValueError(error_str)
        return self.client.get_or_create_collection(name=name, embedding_function=self.embedding_function)

    def get_collection(self, name: str):
        print(f"getting collection: {name}")
        return self.client.get_collection(name=name, embedding_function=self.embedding_function)


# Simple test routine when executing this module directly
if __name__ == "__main__":
    import os

    # Set up logging for testing
    logger = get_logger(__name__)
    # Use a temporary directory
    test_db_path = os.path.join(os.getcwd(), "data", "test_context")
    os.makedirs(test_db_path, exist_ok=True)
    os.environ["HF_TOKEN"] = Config().get("HF_TOKEN")

    client = ChromadbClient(persist_directory=Config().get("CHROMADB_PERSIST_DIR"))

    # List all collections
    collections = client.list_collections()

    print("Available collections:")
    for collection in collections:
        print(f"- Name: {collection}")

    # Create a dummy result without manual embedding
    dummy_result = {
        "text": "This is a test result.",
        "metadata": {"source": "unit test"}
        # No embedding provided - will use paraphrase-MiniLM-L6-v2
    }

    # Store the dummy result
    client.store_results([dummy_result])

    # Query using text
    query_results = client.query_text("What are AlphaSix's major capabilities")
    print("Text query results:", query_results['documents'])
