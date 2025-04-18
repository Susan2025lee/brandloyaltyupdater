import chromadb
from chromadb.config import Settings
from typing import Optional, List, Dict
import sys
import os

# Add src directory to path for reliable imports
# Assuming vector_store.py is in src/
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary components directly
from config import VECTOR_STORE_DIR
from models import DocumentChunk
from core.llm_interface import LLMInterface

# Ensure the vector store directory exists
VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)

# Global client instance (can be managed differently if needed)
_chroma_client: Optional[chromadb.ClientAPI] = None

def get_chroma_client() -> chromadb.ClientAPI:
    """Initializes and returns a persistent ChromaDB client.

    Returns:
        chromadb.ClientAPI: The initialized ChromaDB client.
    """
    global _chroma_client
    if _chroma_client is None:
        print(f"Initializing ChromaDB client with persistence path: {VECTOR_STORE_DIR}")
        # Configure ChromaDB for persistent storage
        _chroma_client = chromadb.PersistentClient(
            path=str(VECTOR_STORE_DIR),
            settings=Settings(
                anonymized_telemetry=False # Optional: Disable telemetry
            )
        )
        print("ChromaDB client initialized.")
    return _chroma_client

def get_or_create_collection(collection_name: str = "brand_loyalty_updates") -> Optional[chromadb.Collection]:
    """Gets or creates a ChromaDB collection.

    Args:
        collection_name (str): The name of the collection.

    Returns:
        Optional[chromadb.Collection]: The ChromaDB collection object, or None if client init fails.
    """
    try:
        client = get_chroma_client()
        # Use get_or_create_collection for convenience
        collection = client.get_or_create_collection(collection_name)
        print(f"Using ChromaDB collection: '{collection_name}'")
        return collection
    except Exception as e:
        print(f"Error getting or creating ChromaDB collection '{collection_name}': {e}")
        return None

def add_embeddings_to_collection(
    collection: chromadb.Collection,
    chunks: List['DocumentChunk'],
    embeddings_dict: Dict[str, List[float]]
) -> bool:
    """Adds document chunks and their embeddings to the ChromaDB collection.

    Args:
        collection (chromadb.Collection): The target ChromaDB collection.
        chunks (List['DocumentChunk']): The list of original document chunks.
        embeddings_dict (Dict[str, List[float]]): Dictionary mapping chunk_id to embedding vector.

    Returns:
        bool: True if adding was successful (or nothing to add), False otherwise.
    """
    if not chunks:
        print("No chunks provided to add to the collection.")
        return True

    ids_to_add: List[str] = []
    embeddings_to_add: List[List[float]] = []
    metadata_to_add: List[Dict[str, str]] = []
    documents_to_add: List[str] = [] # Store the text itself as the document

    print(f"Preparing {len(chunks)} items for ChromaDB collection '{collection.name}'...")

    for chunk in chunks:
        chunk_id = chunk['chunk_id']
        if chunk_id in embeddings_dict:
            ids_to_add.append(chunk_id)
            embeddings_to_add.append(embeddings_dict[chunk_id])
            documents_to_add.append(chunk['text'])
            metadata_to_add.append({
                "source_filename": chunk['source_filename']
                # Add other relevant metadata from DocumentChunk here if needed
            })
        else:
            print(f"Warning: Embedding not found for chunk_id '{chunk_id}'. Skipping this chunk.")

    if not ids_to_add:
        print("No valid embeddings found to add to the collection.")
        return True # Nothing to add, technically not a failure

    try:
        # Use collection.add for batch insertion
        # Note: ChromaDB handles duplicates based on ID by default (upserts)
        print(f"Adding {len(ids_to_add)} items to collection '{collection.name}'...")
        collection.add(
            ids=ids_to_add,
            embeddings=embeddings_to_add,
            metadatas=metadata_to_add,
            documents=documents_to_add
        )
        print("Successfully added items to the collection.")
        return True
    except Exception as e:
        print(f"Error adding items to ChromaDB collection '{collection.name}': {e}")
        return False

def query_collection(
    collection: chromadb.Collection,
    query_text: str,
    n_results: int = 5,
    llm_interface: Optional['LLMInterface'] = None
) -> Optional[chromadb.QueryResult]:
    """Queries the ChromaDB collection using a text query.

    Generates an embedding for the query text and performs a similarity search.

    Args:
        collection (chromadb.Collection): The ChromaDB collection to query.
        query_text (str): The text query.
        n_results (int): The number of results to retrieve.
        llm_interface (Optional['LLMInterface']): An initialized LLMInterface instance
            for generating the query embedding. If None, a new one is created.

    Returns:
        Optional[chromadb.QueryResult]: The query results from ChromaDB, or None if
                                        query embedding generation or querying fails.
    """
    if not llm_interface:
        try:
            print("Initializing LLMInterface for query embedding...")
            llm_interface = LLMInterface()
        except Exception as e:
            print(f"Error initializing LLMInterface for query: {e}")
            return None

    if not llm_interface.embedding_model_name:
        print("Error: LLMInterface provided has no embedding model configured for query.")
        return None

    print(f"Generating embedding for query: \"{query_text[:100]}...\"")
    query_embedding = llm_interface.generate_embedding(query_text)

    if not query_embedding:
        print("Error: Failed to generate embedding for the query text.")
        return None

    try:
        print(f"Querying collection '{collection.name}' for {n_results} results...")
        results = collection.query(
            query_embeddings=[query_embedding], # Expects a list of embeddings
            n_results=n_results,
            include=['metadatas', 'documents', 'distances'] # Include desired data
        )
        print("Query successful.")
        return results
    except Exception as e:
        print(f"Error querying ChromaDB collection '{collection.name}': {e}")
        return None

# --- Example Usage --- 

if __name__ == '__main__':
    print("--- Testing ChromaDB Client Initialization --- ")
    client = None
    try:
        client = get_chroma_client()
        print(f"Client type: {type(client)}")
        
        print("\n--- Testing Collection Get/Create --- ")
        collection = get_or_create_collection("test_collection")
        if collection:
            print(f"Collection name: {collection.name}")
            print(f"Initial item count: {collection.count()}")
            # Clean up the test collection if needed
            # client.delete_collection("test_collection")
        else:
            print("Failed to get or create collection.")

    except Exception as e:
        print(f"\nAn error occurred during ChromaDB client/collection tests: {e}")
        import traceback
        traceback.print_exc()

    # --- Test Adding Embeddings --- 
    print("\n--- Testing Adding Embeddings --- ")
    test_collection = None
    try:
        # Create dummy data similar to output of ingest and embed steps
        test_chunks = [
            DocumentChunk(chunk_id="test_add_0", source_filename="test_doc.md", text="Text content A."),
            DocumentChunk(chunk_id="test_add_1", source_filename="test_doc.md", text="Text content B.")
        ]
        test_embeddings = {
            "test_add_0": [0.1, 0.2, 0.3],
            "test_add_1": [0.4, 0.5, 0.6]
        }

        test_collection = get_or_create_collection("test_add_collection")
        if test_collection:
            initial_count = test_collection.count()
            print(f"Initial count in test_add_collection: {initial_count}")
            success = add_embeddings_to_collection(test_collection, test_chunks, test_embeddings)
            if success:
                final_count = test_collection.count()
                print(f"Final count in test_add_collection: {final_count}")
                # Simple check: count should increase or stay same (upsert)
                assert final_count >= initial_count 
            else:
                print("Adding embeddings failed.")
        else:
             print("Could not get/create test_add_collection for adding test.")

    except Exception as e:
        print(f"\nAn error occurred during test adding embeddings: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up the test collection in a finally block
        if client and test_collection:
            try:
                print(f"Cleaning up {test_collection.name}...")
                client.delete_collection(test_collection.name)
                print(f"Cleaned up {test_collection.name}.")
            except Exception as e:
                 print(f"Error cleaning up collection {test_collection.name}: {e}") 

    # --- Test Querying --- 
    print("\n--- Testing Querying --- ")
    query_collection_instance = None
    query_client = None
    try:
        query_client = get_chroma_client()
        # Re-use the test_add_collection name, but create it fresh
        query_collection_name = "test_query_collection"
        query_client.delete_collection(query_collection_name) # Ensure clean start
        query_collection_instance = get_or_create_collection(query_collection_name)

        if query_collection_instance:
            # Add some data first
            query_test_chunks = [
                DocumentChunk(chunk_id="query_A", source_filename="docQ.md", text="Information about apples and oranges."),
                DocumentChunk(chunk_id="query_B", source_filename="docQ.md", text="More details about oranges specifically."),
                DocumentChunk(chunk_id="query_C", source_filename="docR.md", text="Information about bananas and grapes.")
            ]
            query_test_embeddings = {
                # Dummy embeddings - real ones needed for meaningful results
                "query_A": [0.1, 0.1, 0.9],
                "query_B": [0.1, 0.2, 0.8],
                "query_C": [0.9, 0.1, 0.1]
            }
            add_success = add_embeddings_to_collection(query_collection_instance, query_test_chunks, query_test_embeddings)

            if add_success:
                print("Data added for query test.")
                query = "Tell me about oranges"
                # Assuming LLMInterface can be initialized via env vars for embedding
                query_results = query_collection(query_collection_instance, query)

                if query_results:
                    print(f"\nQuery results for: '{query}'")
                    # Results is a dict with keys like ids, distances, metadatas, documents, embeddings
                    # Each value is a list containing results for each query embedding (we sent 1)
                    if query_results.get('ids') and len(query_results['ids']) > 0:
                        for i, doc_id in enumerate(query_results['ids'][0]):
                            distance = query_results['distances'][0][i]
                            doc_text = query_results['documents'][0][i]
                            metadata = query_results['metadatas'][0][i]
                            print(f"  Result {i+1}:")
                            print(f"    ID: {doc_id}")
                            print(f"    Distance: {distance:.4f}")
                            print(f"    Metadata: {metadata}")
                            print(f"    Document: {doc_text[:100]}...")
                    else:
                        print("Query returned no results.")
                else:
                    print("Querying failed.")
            else:
                 print("Failed to add data for query test.")
        else:
            print("Could not get/create test_query_collection.")

    except Exception as e:
        print(f"\nAn error occurred during query testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up query test collection
        if query_client and query_collection_instance:
            try:
                print(f"Cleaning up {query_collection_instance.name}...")
                query_client.delete_collection(query_collection_instance.name)
                print(f"Cleaned up {query_collection_instance.name}.")
            except Exception as e:
                 print(f"Error cleaning up collection {query_collection_instance.name}: {e}") 