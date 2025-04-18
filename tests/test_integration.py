import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Modules involved in the integration
from retrieve import retrieve_relevant_chunks
from generate import generate_summary_for_metric
from core.llm_interface import LLMInterface
import chromadb # for Collection type hint

# --- Test Case --- 

@patch('retrieve.get_or_create_collection') # Mock collection access in retrieve
@patch('retrieve.query_collection')       # Mock the vector store query in retrieve
@patch('generate.LLMInterface')          # Mock LLMInterface init in generate
def test_retrieve_generate_flow(mock_gen_llm_init, mock_query_coll, mock_get_coll):
    """Test the integration flow from retrieval to generation."""
    
    # --- Setup Mocks --- 
    
    # 1. Mock for vector store query results (used by retrieve)
    mock_query_results_data = {
        'ids': [['integ_chunk_1', 'integ_chunk_2']],
        'documents': [['Relevant context 1.', 'Relevant context 2.']],
        'metadatas': [[{'source_filename': 'integ_docA.pdf'}, {'source_filename': 'integ_docB.md'}]],
        'distances': [[0.1, 0.2]]
    }
    mock_query_coll.return_value = mock_query_results_data
    
    # 2. Mock for collection object (used by retrieve)
    mock_collection_instance = MagicMock(spec=chromadb.Collection)
    mock_get_coll.return_value = mock_collection_instance
    
    # 3. Mock for LLMInterface used by generate
    mock_llm_instance_gen = MagicMock(spec=LLMInterface)
    mock_llm_instance_gen.model_name = "mock-gen-model"
    mock_llm_instance_gen.generate_response.return_value = "Integration test summary."
    mock_gen_llm_init.return_value = mock_llm_instance_gen

    # --- Execute Flow --- 
    query = "integration test query"
    metric = "Integration Metric"
    n_results = 2

    # Step 1: Retrieve chunks
    # We mock the underlying query, so no real LLMInterface needed here for retrieve
    retrieved_chunks = retrieve_relevant_chunks(query, n_results=n_results)

    # Assertions for Retrieval Part
    assert retrieved_chunks is not None
    assert len(retrieved_chunks) == 2
    assert retrieved_chunks[0]['id'] == 'integ_chunk_1'
    assert retrieved_chunks[1]['metadata']['source_filename'] == 'integ_docB.md'
    mock_query_coll.assert_called_once() # Ensure vector store was queried

    # Step 2: Generate Summary (using retrieved chunks)
    # This will use the patched LLMInterface for generate
    final_summary = generate_summary_for_metric(metric, retrieved_chunks)

    # Assertions for Generation Part
    assert final_summary == "Integration test summary."
    mock_gen_llm_init.assert_called_once() # Ensure generate's LLMInterface was init'd (mocked)
    mock_llm_instance_gen.generate_response.assert_called_once()
    
    # Check prompt passed to generate_response
    call_args, call_kwargs = mock_llm_instance_gen.generate_response.call_args
    generated_prompt = call_kwargs.get('prompt')
    assert generated_prompt is not None
    assert f"metric: **{metric}**" in generated_prompt
    assert "Source: integ_docA.pdf" in generated_prompt
    assert "Relevant context 1." in generated_prompt
    assert "Source: integ_docB.md" in generated_prompt
    assert "Relevant context 2." in generated_prompt 