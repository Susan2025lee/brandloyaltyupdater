## 1. Product Requirements

### 1.1 Objectives
- Automate extraction of new brand‐loyalty insights from incoming reports.
- Generate concise update paragraphs for each metric.
- Integrate updates into a living Markdown report hosted on GitHub.
- Provide a simple review UI using Streamlit.

### 1.2 Scope
- Ingestion of Markdown and PDF files via a designated file drop.
- Chunking of documents into ~500‐token passages.
- Embedding using OpenAI’s text‐embedding‐ada‐002.
- Indexing and retrieval via ChromaDB (embedded mode).
- Retrieval‐Augmented Generation for update summaries with GPT‐o4‐mini.
- GitHub for version control and tracking report changes.
- Streamlit for UI prototyping.
- Cron + Python scripts for orchestration in the PoC phase.

### 1.3 Success Criteria
- The system ingests and processes at least one new report end‐to‐end.
- New update paragraphs generated correctly for at least two brand loyalty metrics.
- End‐to‐end pipeline completes within 10 minutes for 10 reports.
- Streamlit UI loads and displays proposed updates for human approval.

## 2. Tech Stack

| Layer                  | Technology                                  |
|------------------------|---------------------------------------------|
| Ingestion              | Python (pdfplumber, BeautifulSoup, pathlib) |
| Chunking               | tiktoken                                    |
| Embeddings             | OpenAI text‐embedding‐ada‐002               |
| Vector Store           | ChromaDB (duckdb+parquet, embedded)         |
| LLM / Summarization    | OpenAI GPT‐o4 mini                          |
| UI                     | Streamlit                                   |
| Version Control        | GitHub                                      |
| Orchestration          | Cron + Python scripts                       |

## 3. Implementation Plan

### 3.1 Milestones
1. **stage 1** – PoC ingestion & chunking:
   - Implement ingestion script for .md and .pdf.
   - Validate JSON schema of ingested docs.
   - Build and test chunker using tiktoken.
2. **stage 2** – Embedding & indexing:
   - Wrap OpenAI embedding calls.
   - Set up ChromaDB local store.
   - Ingest sample chunks and verify query results.
3. **stage 3** – Retrieval & summarization:
   - Implement `retrieve_relevant()` function.
   - Draft and refine summarization prompts.
   - Generate updates for sample base report.
4. **stage 4** – Integration & UI:
   - Integrate auto‐commit workflow to GitHub.
   - Build Streamlit app for human review.
   - Final end‐to‐end testing and tuning.

