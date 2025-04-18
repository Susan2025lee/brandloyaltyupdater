import pytest
from unittest.mock import MagicMock, patch
import sys
import os
from typing import List, Dict, Any, Optional

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Module to test
import retrieve
import chromadb # For type hinting

# --- Fixtures --- 

@pytest.fixture
def mock_query_results() -> Dict[str, List[List[Any]]]:
    """Provides a sample structure similar to ChromaDB query results."""
    return {
        'ids': [['chunk_A', 'chunk_C']],
        'documents': [['Text about A.', 'Text about C.']],
        'metadatas': [[{'source': 'doc1'}, {'source': 'doc2'}]],
        'distances': [[0.123, 0.456]]
        # 'embeddings': None # Often included but not processed by retrieve_relevant_chunks
    }

@pytest.fixture
def mock_empty_query_results() -> Dict[str, List[List[Any]]]:
    """Provides an empty query result structure."""
    return {
        'ids': [[]],
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]]
    }

# --- Test Cases --- 

@patch('retrieve.get_or_create_collection')
@patch('retrieve.query_collection')
def test_retrieve_success(mock_query_coll, mock_get_coll, mock_query_results):
    """Test successful retrieval and processing of results."""
    # Setup mocks
    mock_query_coll.return_value = mock_query_results
    mock_collection_instance = MagicMock(spec=chromadb.Collection)
    mock_get_coll.return_value = mock_collection_instance

    query = "test query"
    n = 2
    results = retrieve.retrieve_relevant_chunks(query, n_results=n)

    # Assertions
    assert results is not None
    assert len(results) == 2
    mock_get_coll.assert_called_once_with(retrieve.DEFAULT_COLLECTION_NAME)
    mock_query_coll.assert_called_once_with(
        collection=mock_collection_instance,
        query_text=query,
        n_results=n,
        llm_interface=None # Check default was passed
    )
    
    # Check processed result structure
    assert results[0]['id'] == 'chunk_A'
    assert results[0]['text'] == 'Text about A.'
    assert results[0]['metadata'] == {'source': 'doc1'}
    assert results[0]['distance'] == 0.123
    assert results[1]['id'] == 'chunk_C'

@patch('retrieve.get_or_create_collection')
@patch('retrieve.query_collection')
def test_retrieve_query_fails(mock_query_coll, mock_get_coll):
    """Test retrieval when the underlying query_collection call fails."""
    mock_query_coll.return_value = None # Simulate failure
    mock_collection_instance = MagicMock(spec=chromadb.Collection)
    mock_get_coll.return_value = mock_collection_instance

    results = retrieve.retrieve_relevant_chunks("query")

    assert results is None
    mock_query_coll.assert_called_once()

@patch('retrieve.get_or_create_collection')
@patch('retrieve.query_collection')
def test_retrieve_no_results(mock_query_coll, mock_get_coll, mock_empty_query_results):
    """Test retrieval when the query returns no results."""
    mock_query_coll.return_value = mock_empty_query_results
    mock_collection_instance = MagicMock(spec=chromadb.Collection)
    mock_get_coll.return_value = mock_collection_instance

    results = retrieve.retrieve_relevant_chunks("query")

    assert results == [] # Expect an empty list
    mock_query_coll.assert_called_once()

@patch('retrieve.get_or_create_collection')
def test_retrieve_collection_fails(mock_get_coll):
    """Test retrieval when getting the collection fails."""
    mock_get_coll.return_value = None # Simulate failure

    # We don't need to patch query_collection as it shouldn't be reached
    results = retrieve.retrieve_relevant_chunks("query")

    assert results is None
    mock_get_coll.assert_called_once() 