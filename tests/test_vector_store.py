import pytest
from unittest.mock import MagicMock, patch, call
import sys
import os
from typing import List, Dict, Optional

# Add src directory to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

# Modules to test
import vector_store
from models import DocumentChunk
from core.llm_interface import LLMInterface # Needed for query test mocking
import chromadb # For type hinting mocks

# --- Fixtures --- 

@pytest.fixture
def dummy_chunks_vs() -> List[DocumentChunk]: # Renamed to avoid conflict
    return [
        DocumentChunk(chunk_id="vs_chunk_0", source_filename="vs_doc1.md", text="Vector Store Test A"),
        DocumentChunk(chunk_id="vs_chunk_1", source_filename="vs_doc1.md", text="Vector Store Test B")
    ]

@pytest.fixture
def dummy_embeddings() -> Dict[str, List[float]]:
    return {
        "vs_chunk_0": [0.5] * 5,
        "vs_chunk_1": [0.6] * 5
    }

@pytest.fixture
def mock_chroma_collection() -> MagicMock:
    """Provides a mocked ChromaDB Collection object."""
    mock = MagicMock(spec=chromadb.Collection)
    mock.name = "mock_collection"
    mock.count.return_value = 0 # Default count
    # We don't need to mock add/query return values unless testing specific results
    return mock

@pytest.fixture
def mock_chroma_client(mock_chroma_collection) -> MagicMock:
    """Provides a mocked ChromaDB Client object."""
    mock = MagicMock(spec=chromadb.ClientAPI)
    # Make get_or_create_collection return our mocked collection
    mock.get_or_create_collection.return_value = mock_chroma_collection
    return mock

@pytest.fixture
def mock_llm_interface_vs() -> MagicMock: # Renamed fixture
    """Provides a mocked LLMInterface for query testing."""
    mock = MagicMock(spec=LLMInterface)
    mock.embedding_model_name = "mock-embedding-model"
    mock.generate_embedding.return_value = [0.7] * 5 # Dummy query embedding
    return mock

# --- Test Cases --- 

# Patch the PersistentClient in the vector_store module
@patch('vector_store.chromadb.PersistentClient')
def test_get_chroma_client(mock_persistent_client, mock_chroma_client):
    """Test that get_chroma_client initializes and returns a client."""
    # Configure the mock PersistentClient constructor to return our client mock
    mock_persistent_client.return_value = mock_chroma_client
    # Reset global state if necessary (important if tests run in sequence)
    vector_store._chroma_client = None 

    client = vector_store.get_chroma_client()
    
    assert client is mock_chroma_client
    mock_persistent_client.assert_called_once() # Check it was called
    # Check if called again it returns the same instance (global singleton pattern)
    client_again = vector_store.get_chroma_client()
    assert client_again is client
    mock_persistent_client.assert_called_once() # Should still only be called once

@patch('vector_store.get_chroma_client')
def test_get_or_create_collection(mock_get_client, mock_chroma_client, mock_chroma_collection):
    """Test getting or creating a collection."""
    mock_get_client.return_value = mock_chroma_client
    collection_name = "test_coll"
    
    collection = vector_store.get_or_create_collection(collection_name)
    
    assert collection is mock_chroma_collection
    mock_get_client.assert_called_once()
    mock_chroma_client.get_or_create_collection.assert_called_once_with(collection_name)

def test_add_embeddings_to_collection(mock_chroma_collection, dummy_chunks_vs, dummy_embeddings):
    """Test adding embeddings, documents, and metadata to the collection."""
    success = vector_store.add_embeddings_to_collection(
        mock_chroma_collection,
        dummy_chunks_vs,
        dummy_embeddings
    )
    
    assert success is True
    # Verify that collection.add was called with correctly structured data
    expected_ids = ["vs_chunk_0", "vs_chunk_1"]
    expected_embeddings = [[0.5] * 5, [0.6] * 5]
    expected_metadatas = [
        {"source_filename": "vs_doc1.md"},
        {"source_filename": "vs_doc1.md"}
    ]
    expected_documents = ["Vector Store Test A", "Vector Store Test B"]
    
    mock_chroma_collection.add.assert_called_once_with(
        ids=expected_ids,
        embeddings=expected_embeddings,
        metadatas=expected_metadatas,
        documents=expected_documents
    )

def test_add_embeddings_empty(mock_chroma_collection):
    """Test adding an empty list of chunks."""
    success = vector_store.add_embeddings_to_collection(mock_chroma_collection, [], {})
    assert success is True
    mock_chroma_collection.add.assert_not_called()

def test_query_collection_success(mock_chroma_collection, mock_llm_interface_vs):
    """Test successful querying of the collection by passing a mock interface."""
    query_text = "Test query"
    n_results = 3
    
    # Mock the collection query response
    mock_query_result = MagicMock(spec=chromadb.QueryResult)
    mock_chroma_collection.query.return_value = mock_query_result
    
    # Pass the configured mock interface directly
    result = vector_store.query_collection(
        collection=mock_chroma_collection,
        query_text=query_text,
        n_results=n_results,
        llm_interface=mock_llm_interface_vs 
    )
    
    assert result is mock_query_result
    # Check embedding was generated
    mock_llm_interface_vs.generate_embedding.assert_called_once_with(query_text)
    # Check collection query call
    mock_chroma_collection.query.assert_called_once_with(
        query_embeddings=[[0.7] * 5], # The dummy embedding from mock_llm_interface_vs
        n_results=n_results,
        include=['metadatas', 'documents', 'distances']
    )

def test_query_collection_embedding_fails(mock_chroma_collection, mock_llm_interface_vs):
    """Test query failure when query embedding generation fails (passing mock interface)."""
    # Make embedding generation return None
    mock_llm_interface_vs.generate_embedding.return_value = None
    
    # Pass the configured mock interface directly
    result = vector_store.query_collection(
        collection=mock_chroma_collection,
        query_text="query",
        llm_interface=mock_llm_interface_vs
    )
    
    assert result is None
    mock_llm_interface_vs.generate_embedding.assert_called_once_with("query")
    mock_chroma_collection.query.assert_not_called() 