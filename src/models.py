from typing import TypedDict, List

class DocumentChunk(TypedDict):
    """Represents a chunk of text from a source document with metadata."""
    chunk_id: str       # Unique identifier for the chunk (e.g., <filename>_chunk_<index>)
    source_filename: str # Name of the original file
    text: str           # The actual text content of the chunk
    # Add more metadata later if needed (e.g., page number for PDFs)

# Example Usage:
# chunk = DocumentChunk(
#     chunk_id="report1.md_chunk_0",
#     source_filename="report1.md",
#     text="This is the first chunk of text..."
# ) 