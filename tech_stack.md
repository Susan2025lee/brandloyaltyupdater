## Technology Stack - Brand Loyalty Monitor PoC

| Layer                  | Technology / Library                          | Purpose                                        |
|------------------------|-----------------------------------------------|------------------------------------------------|
| **Programming Lang.**  | Python 3.10+                                  | Core development language                      |
| **File Ingestion**     | `pathlib` (built-in)                          | File system interaction                      |
|                        | `python-pdfplumber`                           | PDF text extraction                            |
|                        | `markdown-it-py` or `mistune`                 | Markdown parsing (if structure needed)         |
| **Text Chunking**      | `tiktoken`                                    | Token counting and text splitting              |
| **Embeddings**         | OpenAI API (`text-embedding-ada-002`)         | Generating text embeddings (via `LLMInterface`) |
| **Vector Store**       | `chromadb` (embedded mode)                    | Storing and querying embeddings locally        |
| **LLM / Generation**   | OpenAI API (`gpt-o4-mini`)                    | Significance assessment, summary generation (via `LLMInterface`) |
| **Review UI**          | `streamlit`                                   | Building the human review interface            |
| **Version Control**    | Git / GitHub                                  | Code management (report managed locally)     |
| **Orchestration (PoC)**| Python `subprocess` / `schedule` or Cron      | Running the processing pipeline sequentially   |
| **Configuration**      | `.env` files (`python-dotenv`)                | Managing API keys and settings                 |
| **Testing**            | `pytest`                                      | Unit and integration testing framework         |

</rewritten_file> 