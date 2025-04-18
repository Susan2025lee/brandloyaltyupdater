import pytest
from pathlib import Path
import sys
import os

# Add src directory to path to allow importing ingest
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, src_path)

from ingest import (
    extract_text_from_pdf,
    # scan_input_directory, # Tested indirectly via ingest_documents
    extract_text_from_md,
    chunk_text,
    get_tokenizer,
    ingest_documents # Import the main function
)
from models import DocumentChunk # Import the data model
# Assume config is implicitly loaded by ingest when it imports config
# from config import INPUT_DIR # Import for potential setup/teardown if needed later

# Define the path to the fixtures directory
FIXTURES_DIR = Path(__file__).parent / 'fixtures'

# Helper function to create test files in a temp dir
def create_test_files(input_dir: Path):
    (input_dir / "test1.md").write_text("Markdown content line 1.\n\nSecond paragraph.", encoding='utf-8')
    # Create a dummy PDF file (content doesn't matter much for this test level)
    (input_dir / "test2.pdf").touch()
    (input_dir / "other.txt").touch()

@pytest.fixture
def setup_test_environment(tmp_path):
    """Create a temporary directory structure with input files for testing ingest_documents."""
    input_dir = tmp_path / "data" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)
    create_test_files(input_dir)
    return input_dir

def test_extract_text_from_pdf_runs():
    """Test that extract_text_from_pdf runs without error on the dummy PDF.
    Note: This doesn't check content as the fixture PDF is dummy.
    Requires a real PDF fixture for content validation.
    """
    dummy_pdf_path = FIXTURES_DIR / 'sample_report.pdf'
    if not dummy_pdf_path.exists():
        pytest.skip(f"Test requires dummy PDF fixture: {dummy_pdf_path}")

    # pdfplumber will likely fail on a dummy file, expect None or str
    result = extract_text_from_pdf(dummy_pdf_path)
    assert result is None or isinstance(result, str)

def test_extract_text_from_non_pdf():
    """Test that extract_text_from_pdf handles non-PDF files gracefully."""
    dummy_md_path = FIXTURES_DIR / 'sample_report.md'
    if not dummy_md_path.exists():
        pytest.skip(f"Test requires dummy MD fixture: {dummy_md_path}")

    result = extract_text_from_pdf(dummy_md_path)
    assert result is None # Should return None for non-PDF invalid input

def test_extract_text_from_non_existent_file():
    """Test that extract_text_from_pdf handles non-existent files gracefully."""
    non_existent_path = FIXTURES_DIR / 'non_existent_file.pdf'
    result = extract_text_from_pdf(non_existent_path)
    assert result is None # Should return None

def test_extract_text_from_md():
    """Test reading text from the dummy Markdown file."""
    dummy_md_path = FIXTURES_DIR / 'sample_report.md'
    if not dummy_md_path.exists():
        pytest.skip(f"Test requires dummy MD fixture: {dummy_md_path}")

    try:
        result = extract_text_from_md(dummy_md_path)
        assert isinstance(result, str)
        assert "Sample Report" in result # Check for some expected content
        assert len(result) > 0
    except Exception as e:
        pytest.fail(f"extract_text_from_md raised an exception: {e}")

def test_extract_text_from_md_non_existent():
    """Test handling of non-existent MD file."""
    non_existent_path = FIXTURES_DIR / 'non_existent_file.md'
    result = extract_text_from_md(non_existent_path)
    assert result is None # Should return None

# --- Chunking Tests --- 

@pytest.fixture
def sample_text_long():
    # A longer text more suitable for token-based chunking tests
    para1 = "This is the first paragraph. It contains several sentences and introduces the topic. We need enough text to span multiple chunks based on token limits. " * 3
    para2 = "The second paragraph discusses related concepts. Tiktoken is used for encoding and decoding, ensuring consistency. Overlapping tokens help maintain context across chunk boundaries. " * 3
    para3 = "Finally, the third paragraph concludes the sample text. Testing edge cases like small max_tokens and large overlaps is important. Precision in token counting is key. " * 3
    return f"{para1}\n\n{para2}\n\n{para3}"

def test_chunk_text_token_splitting(sample_text_long):
    """Test that chunking splits text based on tokens and respects max_tokens."""
    max_tokens = 50
    overlap = 10
    chunks = chunk_text(sample_text_long, max_tokens=max_tokens, overlap=overlap)
    tokenizer = get_tokenizer()
    
    assert len(chunks) > 1 # Expect multiple chunks
    assert all(isinstance(c, str) and len(c) > 0 for c in chunks)
    
    for i, chunk in enumerate(chunks):
        token_count = len(tokenizer.encode(chunk))
        assert token_count <= max_tokens, f"Chunk {i} exceeds max_tokens: {token_count} > {max_tokens}"
        # Check if overlap seems roughly correct (hard to be exact due to tokenization)
        if i > 0:
            prev_chunk_tokens = tokenizer.encode(chunks[i-1])
            current_chunk_tokens = tokenizer.encode(chunks[i])
            # Check if the start of the current chunk matches the end of the previous one
            overlap_start_token_in_current = current_chunk_tokens[0]
            assert overlap_start_token_in_current in prev_chunk_tokens[-(overlap + 5):], f"Overlap failed check between chunk {i-1} and {i}" # Allow some slack

def test_chunk_text_large_limit_token(sample_text_long):
    """Test chunking with a limit larger than the text (token-based)."""
    tokenizer = get_tokenizer()
    total_tokens = len(tokenizer.encode(sample_text_long))
    chunks = chunk_text(sample_text_long, max_tokens=total_tokens + 100, overlap=50)
    assert len(chunks) == 1 # Expecting one chunk
    # Decoding and re-encoding might have slight variations, compare token lists
    original_tokens = tokenizer.encode(sample_text_long)
    chunk_tokens = tokenizer.encode(chunks[0])
    assert chunk_tokens == original_tokens # Should be identical token sequence

def test_chunk_text_empty_input_token():
    """Test chunking with empty string input (token-based)."""
    chunks = chunk_text("", max_tokens=50, overlap=10)
    assert chunks == []

# --- Ingestion Pipeline Tests --- 

def test_ingest_documents_structure_and_metadata(setup_test_environment, monkeypatch):
    """Test the main ingest_documents function for output structure and metadata."""
    # Mock config.INPUT_DIR to use the temporary test directory
    # Ensure ingest module uses the mocked path
    monkeypatch.setattr('ingest.INPUT_DIR', setup_test_environment)

    # Run the main ingestion function
    document_chunks = ingest_documents()

    # Basic assertions
    assert isinstance(document_chunks, list)
    # Expect chunks from test1.md (dummy test2.pdf likely yields no text/chunks)
    assert len(document_chunks) > 0

    # Check structure and metadata of the first chunk
    first_chunk = document_chunks[0]
    assert isinstance(first_chunk, dict) # Check if it behaves like a TypedDict
    assert 'chunk_id' in first_chunk
    assert 'source_filename' in first_chunk
    assert 'text' in first_chunk

    # Check metadata values (example from test1.md)
    assert first_chunk['source_filename'] == "test1.md"
    assert first_chunk['chunk_id'].startswith("test1.md_chunk_")
    assert isinstance(first_chunk['text'], str)
    assert len(first_chunk['text']) > 0
    assert "Markdown content line 1" in first_chunk['text'] # Verify text content

# (Placeholder for scan_input_directory test is now covered by test_ingest_documents)
# Placeholder for scan_input_directory test - needs mocking config.INPUT_DIR
# def test_scan_input_directory(setup_test_environment, monkeypatch):
#     """Test scanning the input directory."""
#     # Mock config.INPUT_DIR to use the temporary test directory
#     monkeypatch.setattr('ingest.INPUT_DIR', setup_test_environment)
# 
#     found_files = scan_input_directory()
#     assert len(found_files) == 2
#     filenames = {f.name for f in found_files}
#     assert "test1.md" in filenames
#     assert "test2.pdf" in filenames
#     assert "other.txt" not in filenames 