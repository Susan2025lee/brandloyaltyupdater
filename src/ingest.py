"""Handles document ingestion: scanning input files, extracting text (PDF, MD),
and chunking text content.
"""

import os
from pathlib import Path
from typing import List, Optional

import pdfplumber
import tiktoken

# Import configuration and models
try:
    from .config import INPUT_DIR
    from .models import DocumentChunk
except ImportError:
    # Handle case where script might be run directly or config is elsewhere
    # This assumes config.py is one level up if run directly from src
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import INPUT_DIR
    from models import DocumentChunk

def scan_input_directory() -> List[Path]:
    """Scans the INPUT_DIR for .md and .pdf files.

    Returns:
        List[Path]: A list of Path objects for found markdown and pdf files.
                    Returns an empty list if the directory doesn't exist or is empty.
    """
    if not INPUT_DIR.is_dir():
        print(f"Warning: Input directory not found: {INPUT_DIR}")
        return []

    found_files = []
    # Iterate through all files in the directory
    for item in INPUT_DIR.iterdir():
        if item.is_file():
            # Check if the file extension is .md or .pdf
            if item.suffix.lower() == '.md' or item.suffix.lower() == '.pdf':
                found_files.append(item)

    print(f"Found {len(found_files)} files in {INPUT_DIR}:")
    for f in found_files:
        print(f" - {f.name}")

    return found_files

def extract_text_from_pdf(file_path: Path) -> Optional[str]:
    """Extracts text content from a PDF file.

    Args:
        file_path: The path to the PDF file.

    Returns:
        The extracted text content as a string, or None if extraction fails
        or the file path is invalid.
    """
    if not file_path.exists() or file_path.suffix.lower() != '.pdf':
        print(f"Error: Invalid PDF file path: {file_path}")
        return None

    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n" # Add newline between pages
        print(f"Successfully extracted text from: {file_path.name}")
        return text.strip()
    except Exception as e:
        print(f"Error extracting text from {file_path.name}: {e}")
        return None

def extract_text_from_md(file_path: Path) -> Optional[str]:
    """Extracts text content from a Markdown file (reads as plain text).

    Args:
        file_path: The path to the Markdown file.

    Returns:
        The extracted text content as a string, or None if reading fails
        or the file path is invalid.
    """
    if not file_path.exists() or file_path.suffix.lower() != '.md':
        print(f"Error: Invalid Markdown file path: {file_path}")
        return None

    try:
        content = file_path.read_text(encoding='utf-8')
        print(f"Successfully read text from: {file_path.name}")
        return content
    except Exception as e:
        print(f"Error reading text from {file_path.name}: {e}")
        return None

# --- Text Chunking --- 

def get_tokenizer(model_name: str = "cl100k_base") -> tiktoken.Encoding:
    """Gets a tiktoken tokenizer instance for a specified model encoding.

    Defaults to "cl100k_base" which is used by gpt-4, gpt-3.5-turbo,
    and text-embedding-ada-002.

    Args:
        model_name: The name of the model encoding to get (e.g., "cl100k_base").

    Returns:
        A tiktoken.Encoding object for the specified model.
    """
    try:
        return tiktoken.get_encoding(model_name)
    except ValueError:
        print(f"Warning: Encoding '{model_name}' not found. Using default 'cl100k_base'.")
        return tiktoken.get_encoding("cl100k_base")

def chunk_text(text: str, max_tokens: int = 500, overlap: int = 50) -> List[str]:
    """Chunks text into smaller pieces based strictly on token count.

    Args:
        text: The input text to chunk.
        max_tokens: The maximum number of tokens per chunk.
        overlap: The number of tokens to overlap between chunks.

    Returns:
        A list of text chunks.
    """
    if not text:
        return []

    tokenizer = get_tokenizer()
    tokens = tokenizer.encode(text)
    
    if not tokens:
        return []

    chunks = []
    start_idx = 0
    total_tokens = len(tokens)

    while start_idx < total_tokens:
        # Determine the end index for the chunk
        end_idx = min(start_idx + max_tokens, total_tokens)
        
        # Decode the chunk tokens back to text
        chunk_tokens = tokens[start_idx:end_idx]
        chunk_text = tokenizer.decode(chunk_tokens)
        chunks.append(chunk_text)
        
        # Move the start index for the next chunk
        if end_idx == total_tokens:
            break
        
        # Otherwise, move start_idx, subtracting overlap
        start_idx += (max_tokens - overlap)
        start_idx = max(start_idx, end_idx - max_tokens + 1)
        start_idx = min(start_idx, end_idx - overlap)
        if start_idx >= end_idx:
             print(f"Warning: Chunking could not advance start index. Overlap ({overlap}) might be too large for max_tokens ({max_tokens}). Breaking.")
             break

    print(f"Chunked text into {len(chunks)} chunks using token-based splitting.")
    return chunks

# --- Main Ingestion Function --- 

def ingest_documents() -> List[DocumentChunk]:
    """Scans input directory, extracts text, chunks, and adds metadata.

    Returns:
        List[DocumentChunk]: A list of document chunks with metadata.
    """
    source_files = scan_input_directory()
    all_chunks: List[DocumentChunk] = []

    for file_path in source_files:
        print(f"Processing file: {file_path.name}")
        text_content: Optional[str] = None

        if file_path.suffix.lower() == '.pdf':
            text_content = extract_text_from_pdf(file_path)
        elif file_path.suffix.lower() == '.md':
            text_content = extract_text_from_md(file_path)

        if text_content:
            raw_chunks = chunk_text(text_content) # Use default chunking params for now
            for i, chunk_str in enumerate(raw_chunks):
                chunk_id = f"{file_path.name}_chunk_{i}"
                doc_chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    source_filename=file_path.name,
                    text=chunk_str
                )
                all_chunks.append(doc_chunk)
            print(f"Created {len(raw_chunks)} chunks for {file_path.name}")
        else:
            print(f"Skipping chunking for {file_path.name} due to extraction failure or empty content.")

    print(f"\nTotal chunks created: {len(all_chunks)}")
    return all_chunks

# Example usage (for testing purposes)
if __name__ == '__main__':
    # Create dummy files for testing if they don't exist
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    (INPUT_DIR / "report1.md").write_text("Content for report 1.\n\nMore content.", encoding='utf-8')
    (INPUT_DIR / "report2.pdf").touch(exist_ok=True) # pdfplumber needs a file, content is ignored here
    (INPUT_DIR / "notes.txt").touch(exist_ok=True) # Should be ignored

    print("--- Running Ingestion Pipeline --- ")
    document_chunks = ingest_documents()
    print("--- Ingestion Pipeline Complete ---")

    if document_chunks:
        print("\n--- Sample Chunk Metadata --- ")
        print(document_chunks[0])
        # print(f"Text:\n{document_chunks[0]['text'][:100]}...") # Print start of text
    else:
        print("\nNo document chunks were generated.")

    # --- Test chunking with the new logic --- 
    sample_text_for_chunking = """
First paragraph. This is the first sentence.
This is the second sentence.

Second paragraph. It talks about different things. Tokens are counted using tiktoken.
We aim for chunks around 500 tokens.

Third paragraph. This one is a bit longer to help test the chunking logic. Splitting happens between paragraphs ideally, but now we focus on tokens. Overlap helps maintain context between chunks.

Fourth paragraph. Another short one.

Fifth paragraph. This is the final paragraph in this sample text. Let's see how it gets chunked using token limits.
"""
    print("\nAttempting to chunk sample text with token-based logic...")
    # Test with parameters likely to cause multiple chunks
    chunks = chunk_text(sample_text_for_chunking, max_tokens=50, overlap=10) 
    if chunks:
        print(f"Generated {len(chunks)} chunks:")
        tokenizer = get_tokenizer()
        for i, chunk in enumerate(chunks):
            token_count = len(tokenizer.encode(chunk))
            print(f"--- Chunk {i+1} (Tokens: {token_count}) ---")
            print(chunk)
            print("------")
    else:
        print("Chunking returned no chunks.")

    # --- Previous direct function tests (can be removed or kept for isolation) --- 
    # print(f"Scanning directory: {INPUT_DIR}")
    # files = scan_input_directory()
    # print("\nScan complete.")

    # Test PDF extraction on the dummy PDF
    pdf_file = INPUT_DIR / "report2.pdf"
    if pdf_file.exists():
        # Note: Dummy PDF created with touch won't have real content
        # For real testing, place an actual PDF in data/input
        print(f"\nAttempting to extract text from {pdf_file.name}...")
        # To make this testable without complex PDF creation, we'll just check if it runs
        try:
            _ = extract_text_from_pdf(pdf_file)
            print(f"(Test) extract_text_from_pdf ran without crashing on {pdf_file.name}")
        except Exception as e:
            print(f"(Test) extract_text_from_pdf crashed: {e}")
    else:
        print(f"\nSkipping PDF extraction test: {pdf_file.name} not found.")

    # Test MD extraction on the dummy MD
    md_file = INPUT_DIR / "report1.md"
    if md_file.exists():
        print(f"\nAttempting to extract text from {md_file.name}...")
        try:
            text = extract_text_from_md(md_file)
            print(f"(Test) extract_text_from_md ran without crashing on {md_file.name}. Content length: {len(text)}")
        except Exception as e:
            print(f"(Test) extract_text_from_md crashed: {e}")
    else:
        print(f"\nSkipping MD extraction test: {md_file.name} not found.")

    # Test chunking
    sample_text_for_chunking = """
First paragraph. This is the first sentence.
This is the second sentence.

Second paragraph. It talks about different things. Tokens are counted using tiktoken.
We aim for chunks around 500 tokens.

Third paragraph. This one is a bit longer to help test the chunking logic. Splitting happens between paragraphs ideally. Overlap helps maintain context between chunks, although the current implementation is basic paragraph overlap.

Fourth paragraph. Another short one.

Fifth paragraph. This is the final paragraph in this sample text. Let's see how it gets chunked.
"""
    print("\nAttempting to chunk sample text...")
    chunks = chunk_text(sample_text_for_chunking, max_tokens=30, overlap=10) # Use small max_tokens for testing
    if chunks:
        print(f"Generated {len(chunks)} chunks:")
        for i, chunk in enumerate(chunks):
            print(f"--- Chunk {i+1} ---")
            print(chunk)
            print("------")
    else:
        print("Chunking returned no chunks.")
    # You can add assertions here if making it a formal test
    # assert len(files) == 2
    # assert any(f.name == 'report1.md' for f in files)
    # assert any(f.name == 'report2.pdf' for f in files) 