"""Handles retrieving relevant document chunks from the vector store."""

import sys
import os
from typing import List, Optional, Dict, Any

# Ensure src directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary functions and classes
from vector_store import get_or_create_collection, query_collection
from core.llm_interface import LLMInterface
import chromadb # Used for type hinting

# Import constant for default collection name
from config import VECTOR_DB_COLLECTION_NAME

def retrieve_relevant_chunks(
    query_text: str,
    n_results: int = 5,
    collection_name: str = VECTOR_DB_COLLECTION_NAME,
    llm_interface: Optional[LLMInterface] = None,
    collection: Optional[chromadb.Collection] = None
) -> Optional[List[Dict[str, Any]]]:
    """Retrieves relevant document chunks from the vector store based on a query.

    Args:
        query_text (str): The query text to search for.
        n_results (int): The maximum number of chunks to retrieve.
        collection_name (str): The name of the ChromaDB collection to query.
        llm_interface (Optional[LLMInterface]): An initialized LLMInterface instance.
                                                 If None, a new one is created.
        collection (Optional[chromadb.Collection]): An existing ChromaDB collection instance.
                                                    If None, gets/creates based on collection_name.

    Returns:
        Optional[List[Dict[str, Any]]]: A list of dictionaries, each containing info
                                        about a relevant chunk (id, text, metadata, distance).
                                        Returns None if retrieval fails.
    """
    print(f"Retrieving {n_results} chunks for query: '{query_text[:100]}...'")

    # Get collection if not provided
    if collection is None:
        collection = get_or_create_collection(collection_name)
        if not collection:
            print(f"Failed to get or create collection '{collection_name}'.")
            return None

    # Query the collection
    # query_collection handles LLM interface initialization if needed
    query_results = query_collection(
        collection=collection,
        query_text=query_text,
        n_results=n_results,
        llm_interface=llm_interface
    )

    if not query_results:
        print("Querying the vector store failed.")
        return None

    # Process results
    # ChromaDB results are structured per query, we only sent one query
    processed_results: List[Dict[str, Any]] = []
    ids = query_results.get('ids', [[]])[0]
    documents = query_results.get('documents', [[]])[0]
    metadatas = query_results.get('metadatas', [[]])[0]
    distances = query_results.get('distances', [[]])[0]

    if not ids:
        print("Query returned no relevant chunks.")
        return []

    for i in range(len(ids)):
        processed_results.append({
            "id": ids[i],
            "text": documents[i],
            "metadata": metadatas[i],
            "distance": distances[i]
        })

    print(f"Successfully retrieved {len(processed_results)} chunks.")
    return processed_results

# --- Example Usage --- 

if __name__ == '__main__':
    print("--- Testing Retrieval --- ")
    # Example query (replace with actual metric or topic)
    # Requires data to be indexed first using index_data.py
    test_query = "customer satisfaction levels"
    num_results = 3

    # Make sure your .env and config.json are set up for LLMInterface
    try:
        results = retrieve_relevant_chunks(test_query, n_results=num_results)

        if results is not None:
            print(f"\n--- Retrieved Results (Top {len(results)}) --- ")
            for i, res in enumerate(results):
                print(f"Result {i+1}:")
                print(f"  ID: {res['id']}")
                print(f"  Distance: {res['distance']:.4f}")
                print(f"  Metadata: {res['metadata']}")
                print(f"  Text: {res['text'][:150]}...")
                print("---")
        else:
            print("\nRetrieval failed.")

    except Exception as e:
        print(f"\nAn error occurred during the retrieval example: {e}")
        import traceback
        traceback.print_exc() 