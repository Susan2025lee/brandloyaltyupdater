import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from typing import List, Dict

# Add src directory to path to allow importing modules
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Modules to test
import embed
from models import DocumentChunk
from core.llm_interface import LLMInterface

# --- Test Data Fixtures --- 

@pytest.fixture
def dummy_chunks() -> List[DocumentChunk]:
    """Provides a list of dummy DocumentChunk objects for testing."""
    return [
        DocumentChunk(chunk_id="doc1_chunk_0", source_filename="doc1", text="Text one."),
        DocumentChunk(chunk_id="doc1_chunk_1", source_filename="doc1", text="Text two, slightly longer."),
        DocumentChunk(chunk_id="doc2_chunk_0", source_filename="doc2", text="Text three from doc 2.")
    ]

@pytest.fixture
def mock_llm_interface() -> MagicMock:
    """Provides a mocked LLMInterface instance with embedding configured."""
    mock = MagicMock(spec=LLMInterface)
    mock.embedding_model_name = "mock-embedding-model"
    # Simulate successful embedding generation
    mock.generate_embedding.side_effect = lambda text: [0.1] * 10 # Return a dummy 10-dim vector
    return mock

@pytest.fixture
def mock_llm_interface_no_embedding() -> MagicMock:
    """Provides a mocked LLMInterface instance without embedding configured."""
    mock = MagicMock(spec=LLMInterface)
    mock.embedding_model_name = None # No embedding model configured
    mock.model_name = "mock-chat-model" # It might have a chat model
    return mock

# --- Test Cases --- 

def test_generate_embeddings_success(dummy_chunks, mock_llm_interface):
    """Test successful embedding generation for all chunks."""
    result = embed.generate_embeddings_for_chunks(dummy_chunks, llm_interface=mock_llm_interface)
    
    assert result is not None
    assert isinstance(result, dict)
    assert len(result) == len(dummy_chunks) # Should have embedding for each chunk
    
    # Check that generate_embedding was called for each chunk
    assert mock_llm_interface.generate_embedding.call_count == len(dummy_chunks)
    
    # Check the content of the result
    for chunk in dummy_chunks:
        chunk_id = chunk['chunk_id']
        assert chunk_id in result
        assert isinstance(result[chunk_id], list)
        assert len(result[chunk_id]) == 10 # Matches dummy vector dimension
        # Check call arguments (optional but good)
        mock_llm_interface.generate_embedding.assert_any_call(chunk['text'])

def test_generate_embeddings_partial_failure(dummy_chunks, mock_llm_interface):
    """Test the case where embedding fails for one chunk (should return None)."""
    # Configure mock to fail on the second call
    mock_llm_interface.generate_embedding.side_effect = [
        [0.1] * 10, # Success for first chunk
        None,       # Failure for second chunk
        [0.3] * 10  # This won't be reached
    ]
    
    result = embed.generate_embeddings_for_chunks(dummy_chunks, llm_interface=mock_llm_interface)
    
    assert result is None # Expect None because one chunk failed
    # Should have stopped after the failure
    assert mock_llm_interface.generate_embedding.call_count == 2

def test_generate_embeddings_no_interface_provided(dummy_chunks, mock_llm_interface):
    """Test that a new LLMInterface is initialized if none is provided."""
    # We patch the LLMInterface class itself for this test
    with patch('embed.LLMInterface', return_value=mock_llm_interface) as mock_init:
        result = embed.generate_embeddings_for_chunks(dummy_chunks, llm_interface=None)
        
        mock_init.assert_called_once() # Check that __init__ was called
        assert result is not None # Should proceed if init succeeds
        assert len(result) == len(dummy_chunks)
        assert mock_llm_interface.generate_embedding.call_count == len(dummy_chunks)

def test_generate_embeddings_interface_init_fails(dummy_chunks):
    """Test case where LLMInterface initialization fails when none is provided."""
    with patch('embed.LLMInterface', side_effect=ValueError("Config error")) as mock_init:
        result = embed.generate_embeddings_for_chunks(dummy_chunks, llm_interface=None)
        
        mock_init.assert_called_once()
        assert result is None # Should return None if init fails

def test_generate_embeddings_interface_no_embedding_model(dummy_chunks, mock_llm_interface_no_embedding):
    """Test providing an LLMInterface that doesn't have an embedding model configured."""
    result = embed.generate_embeddings_for_chunks(dummy_chunks, llm_interface=mock_llm_interface_no_embedding)
    
    assert result is None
    # Ensure generate_embedding wasn't called
    mock_llm_interface_no_embedding.generate_embedding.assert_not_called()

def test_generate_embeddings_empty_chunk_list():
    """Test calling the function with an empty list of chunks."""
    mock_interface = MagicMock(spec=LLMInterface)
    mock_interface.embedding_model_name = "mock-model"
    
    result = embed.generate_embeddings_for_chunks([], llm_interface=mock_interface)
    
    assert result == {} # Should return an empty dictionary
    mock_interface.generate_embedding.assert_not_called() 