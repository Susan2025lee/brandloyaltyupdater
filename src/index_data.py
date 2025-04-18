import sys
import os
import time

# Ensure src directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import necessary functions and classes
from core.llm_interface import LLMInterface
from ingest import ingest_documents
from embed import generate_embeddings_for_chunks
from vector_store import get_or_create_collection, add_embeddings_to_collection

# --- Configuration --- 
# Use a specific collection name for this indexing process
COLLECTION_NAME = "brand_loyalty_updates"

def main():
    """Main function to run the indexing pipeline."""
    print("--- Starting Indexing Pipeline --- ")
    start_time = time.time()

    # 1. Initialize LLM Interface (needed for embedding)
    #    Assumes environment variables and config.json are set up
    print("Initializing LLM Interface...")
    try:
        llm_interface = LLMInterface()
        if not llm_interface.embedding_model_name:
             print("Error: LLM Interface is not configured with an embedding model.")
             print("Please ensure DEFAULT_EMBEDDING_MODEL_KEY is set and config.json is correct.")
             return
    except Exception as e:
        print(f"Failed to initialize LLM Interface: {e}")
        return
    print("LLM Interface initialized.")

    # 2. Ingest and Chunk Documents
    print("\nIngesting and chunking documents...")
    chunks = ingest_documents()
    if not chunks:
        print("No documents found or processed. Exiting.")
        return
    print(f"Ingested and chunked into {len(chunks)} total chunks.")

    # 3. Generate Embeddings
    print("\nGenerating embeddings...")
    embeddings_dict = generate_embeddings_for_chunks(chunks, llm_interface)
    if not embeddings_dict:
        print("Failed to generate embeddings. Exiting.")
        return
    print(f"Generated embeddings for {len(embeddings_dict)} chunks.")

    # 4. Get or Create Vector Store Collection
    print("\nAccessing vector store collection...")
    collection = get_or_create_collection(COLLECTION_NAME)
    if not collection:
        print("Failed to access vector store collection. Exiting.")
        return
    print(f"Using collection: '{collection.name}'")

    # 5. Add Embeddings to Collection
    print("\nAdding embeddings to collection...")
    success = add_embeddings_to_collection(collection, chunks, embeddings_dict)
    if not success:
        print("Failed to add embeddings to the collection.")
        # Depending on requirements, might decide if partial success is okay
    else:
        print("Embeddings successfully added to the collection.")

    # --- Pipeline Complete --- 
    end_time = time.time()
    duration = end_time - start_time
    print(f"\n--- Indexing Pipeline Complete ({duration:.2f} seconds) --- ")

if __name__ == "__main__":
    main() 