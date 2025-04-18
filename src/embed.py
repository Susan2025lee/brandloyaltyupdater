from typing import List, Optional, Dict
import time

# Import LLMInterface and DocumentChunk
try:
    from .core.llm_interface import LLMInterface
    from .models import DocumentChunk
except ImportError:
    # Handle potential direct script run or different import paths
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.core.llm_interface import LLMInterface
    from src.models import DocumentChunk

# --- Embedding Function --- 

def generate_embeddings_for_chunks(
    chunks: List[DocumentChunk],
    llm_interface: Optional[LLMInterface] = None
) -> Optional[Dict[str, List[float]]]:
    """Generates embeddings for a list of document chunks using LLMInterface.

    Args:
        chunks (List[DocumentChunk]): The list of chunks to embed.
        llm_interface (Optional[LLMInterface]): An initialized LLMInterface instance.
            If None, a new one will be created (requires env vars to be set).

    Returns:
        Optional[Dict[str, List[float]]]: A dictionary mapping chunk_id to its embedding vector.
                                         Returns None if embedding fails for any chunk or if
                                         the interface cannot be initialized.
    """
    if not llm_interface:
        try:
            print("Initializing LLMInterface for embedding...")
            # Initialize specifically for embedding if no interface provided
            # Assumes DEFAULT_EMBEDDING_MODEL_KEY is set in .env
            llm_interface = LLMInterface()
        except Exception as e:
            print(f"Error initializing LLMInterface: {e}")
            return None

    if not llm_interface.embedding_model_name:
        print("Error: LLMInterface provided has no embedding model configured.")
        return None

    embeddings_dict: Dict[str, List[float]] = {}
    total_chunks = len(chunks)
    start_time = time.time()

    print(f"Starting embedding generation for {total_chunks} chunks using {llm_interface.embedding_model_name}...")

    for i, chunk in enumerate(chunks):
        chunk_id = chunk['chunk_id']
        text_to_embed = chunk['text']

        print(f"  Embedding chunk {i+1}/{total_chunks} (id: {chunk_id})...")
        embedding = llm_interface.generate_embedding(text_to_embed)

        if embedding:
            embeddings_dict[chunk_id] = embedding
            # Optional: Add a small delay to potentially avoid hitting strict rate limits
            # time.sleep(0.05) # Adjust as needed
        else:
            print(f"Error: Failed to generate embedding for chunk {chunk_id}. Aborting.")
            return None # Fail fast if any chunk fails

    end_time = time.time()
    duration = end_time - start_time
    print(f"Successfully generated embeddings for {len(embeddings_dict)} chunks in {duration:.2f} seconds.")

    return embeddings_dict

# --- Example Usage --- 

if __name__ == '__main__':
    # Create some dummy chunks for testing
    dummy_chunks = [
        DocumentChunk(chunk_id="doc1_chunk_0", source_filename="doc1", text="This is the first piece of text."),
        DocumentChunk(chunk_id="doc1_chunk_1", source_filename="doc1", text="This is the second piece, slightly longer."),
        DocumentChunk(chunk_id="doc2_chunk_0", source_filename="doc2", text="A chunk from a different document.")
    ]

    print("--- Testing Embedding Generation --- ")
    # Assumes environment variables and config.json are set up correctly
    # Requires OPENAI_API_KEY in config.json for the embedding model
    # Requires DEFAULT_EMBEDDING_MODEL_KEY in .env
    try:
        embeddings_result = generate_embeddings_for_chunks(dummy_chunks)

        if embeddings_result:
            print("\n--- Embedding Results --- ")
            print(f"Generated {len(embeddings_result)} embeddings.")
            # Print info about the first embedding
            first_id = list(embeddings_result.keys())[0]
            first_embedding = embeddings_result[first_id]
            print(f"Embedding for chunk '{first_id}':")
            print(f"  Dimension: {len(first_embedding)}")
            print(f"  First 5 values: {first_embedding[:5]}")
        else:
            print("\nEmbedding generation failed.")

    except Exception as e:
        print(f"\nAn error occurred during the embedding example: {e}")
        import traceback
        traceback.print_exc() 