"""Main orchestration script for the Brand Loyalty Monitor pipeline."""

import sys
import os
import re
from typing import List, Dict, Any

# Add src directory to path if not already present
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# --- Core Components ---
from config import INPUT_DIR, BRAND_LOYALTY_METRICS_PATH, VECTOR_DB_COLLECTION_NAME
from core.llm_interface import LLMInterface
from ingest import ingest_documents, scan_input_directory
from embed import generate_embeddings_for_chunks
from vector_store import get_chroma_client, add_embeddings_to_collection, get_or_create_collection
from retrieve import retrieve_relevant_chunks
from generate import generate_assessment_for_metric, NO_UPDATE_MARKER

# --- Constants ---

def get_metric_names(filepath: str = BRAND_LOYALTY_METRICS_PATH) -> List[str]:
    """Parses metric names from the brandloyalty.md file.

    Assumes metrics are defined in the first column of a Markdown table,
    enclosed in double asterisks (e.g., | **Metric Name** | ...).
    Adjust regex if format is different.

    Args:
        filepath: Path to the markdown file containing metric definitions.

    Returns:
        A list of metric names found in the file.
    """
    metric_names = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        # Regex to find lines starting with | **, capturing text until the next **
        # Excludes the header separator line (| :--- |)
        matches = re.findall(r"^\|\s*\*\*(.*?)\*\*\s*\|", content, re.MULTILINE)
        # Filter out any potential empty matches or lines that are just separators
        metric_names = [match.strip() for match in matches if match.strip() and not match.strip().startswith(':---')]
        if not metric_names:
             print(f"Warning: No metric names found in {filepath} matching the expected table format (| **Metric** |). Check file format and content.")
    except FileNotFoundError:
        print(f"Error: Metrics definition file not found at {filepath}. Cannot proceed.")
        # Re-raise or return empty list depending on desired error handling
        raise
    except Exception as e:
        print(f"Error reading or parsing metrics file {filepath}: {e}")
        raise
    return metric_names

def run_full_pipeline() -> List[Dict[str, Any]]:
    """Orchestrates the entire pipeline from ingestion to proposed updates.

    1. Initializes components (LLM, Vector Store).
    2. Gets list of metrics.
    3. Ingests and indexes new documents from INPUT_DIR.
    4. For each metric, retrieves relevant chunks and generates assessment.
    5. Collects significant updates.

    Returns:
        A list of dictionaries, where each dictionary represents a proposed update
        with keys like 'metric', 'update_text', 'source'. Returns empty list if
        no updates or an error occurs.
    """
    print("--- Starting Brand Loyalty Monitor Pipeline ---")

    proposed_updates = []

    try:
        # 1. Initialization
        print("Initializing components...")
        llm_interface = LLMInterface() # Assumes default model key is set
        chroma_client = get_chroma_client()
        # Use the helper from vector_store.py which handles potential errors
        collection = get_or_create_collection(VECTOR_DB_COLLECTION_NAME)
        if collection is None:
             print("Failed to get or create ChromaDB collection. Stopping pipeline.")
             return []
        print(f"Using ChromaDB collection: '{VECTOR_DB_COLLECTION_NAME}'")

        # 2. Get Metrics
        print(f"Loading metrics from {BRAND_LOYALTY_METRICS_PATH}...")
        metrics_to_assess = get_metric_names()
        if not metrics_to_assess:
            print("Error: No metrics found to assess. Stopping pipeline.")
            return []
        print(f"Found metrics: {metrics_to_assess}")

        # 3. Ingestion & Indexing
        print(f"Scanning for new documents in {INPUT_DIR}...")
        input_files = scan_input_directory()
        if not input_files:
            print("No new input files found.")
            # Decide if pipeline should stop or continue (e.g., if updates could arise from existing data?)
            # For now, let's assume we only run assessment if new files are present.
            # If run periodically, this is reasonable.
            print("--- Pipeline finished: No new documents to process. ---")
            return [] 

        print(f"Found input files: {input_files}")
        print("Ingesting documents...")
        all_chunks_no_embedding = ingest_documents()
        if not all_chunks_no_embedding:
            print("No text chunks extracted from documents. Stopping pipeline.")
            return []
        print(f"Extracted {len(all_chunks_no_embedding)} chunks.")

        print("Generating embeddings...")
        embeddings_dict = generate_embeddings_for_chunks(all_chunks_no_embedding, llm_interface=llm_interface)
        if not embeddings_dict:
            print("Failed to generate embeddings. Stopping pipeline.")
            return []
        print(f"Generated embeddings for {len(embeddings_dict)} chunks.")

        # Add chunks and their separate embeddings dict to the vector store
        print("Adding chunks and embeddings to vector store...")
        success = add_embeddings_to_collection(collection, all_chunks_no_embedding, embeddings_dict)
        if not success:
            print("Failed to add embeddings to vector store. Stopping pipeline.")
            return []
        print("Finished adding chunks and embeddings.")

        # 4. Retrieval & Assessment per Metric
        print("--- Starting Assessment Phase --- ")
        for metric in metrics_to_assess:
            print(f"\nAssessing metric: '{metric}'")

            # Retrieve relevant context
            # Consider defining retrieval parameters (k) in config or here
            retrieval_k = 5 # Number of chunks to retrieve
            # Use keyword arguments for clarity and correctness
            relevant_chunks_data = retrieve_relevant_chunks(query_text=metric, collection=collection, n_results=retrieval_k)
            if relevant_chunks_data is None: # Check for None in case of query error
                 print(f"Error retrieving chunks for '{metric}'. Skipping assessment.")
                 continue
            if not relevant_chunks_data:
                print(f"No relevant chunks found in vector store for '{metric}'. Skipping assessment.")
                continue
            print(f"Retrieved {len(relevant_chunks_data)} chunks for '{metric}'.")

            # Generate assessment
            assessment_result = generate_assessment_for_metric(
                metric_name=metric,
                retrieved_chunks=relevant_chunks_data, # Pass the list of dicts
                llm_interface=llm_interface
            )

            # 5. Collect Updates
            if assessment_result and assessment_result != NO_UPDATE_MARKER:
                # Extract source information - simple approach: use source of first chunk
                # More sophisticated: aggregate sources or let LLM include them
                first_source = relevant_chunks_data[0].get('metadata', {}).get('source_filename', 'Unknown Source')
                print(f"Significant update found for '{metric}'. Adding to proposed updates.")
                proposed_updates.append({
                    'metric': metric,
                    'update_text': assessment_result,
                    'source': first_source, # Simple source attribution for now
                    'status': 'pending' # Initial status for UI
                })
            elif assessment_result == NO_UPDATE_MARKER:
                print(f"No significant update needed for '{metric}'.")
            else:
                # Handle None case (error during generation)
                print(f"Assessment failed for metric '{metric}'. Skipping.")

    except Exception as e:
        print(f"\n--- PIPELINE FAILED --- ")
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        # Depending on requirements, could return partial results or empty list
        return []

    print("\n--- Pipeline Finished Successfully ---")
    print(f"Proposed {len(proposed_updates)} updates.")
    return proposed_updates

# --- Main Execution Guard --- 
if __name__ == '__main__':
    # This allows running the script directly for testing/debugging
    print("Running pipeline directly...")
    
    # Ensure necessary environment variables and config are set up
    # (e.g., OPENAI_API_KEY, DEFAULT_LLM_MODEL_KEY, DEFAULT_EMBEDDING_MODEL_KEY)
    # Ensure baseline_report.md and brandloyalty.md exist
    # Ensure data/input directory exists
    
    results = run_full_pipeline()
    
    if results:
        print("\n--- Proposed Updates Summary --- ")
        for idx, update in enumerate(results):
            print(f"Update {idx+1}: Metric='{update['metric']}', Source='{update['source']}'")
            print(f"  Text: {update['update_text'][:100]}...") # Print snippet
    else:
        print("\nNo updates proposed or pipeline failed.") 