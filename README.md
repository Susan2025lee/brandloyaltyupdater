# Brand Loyalty Monitor PoC

This project is a Proof of Concept (PoC) for an automated system to monitor the brand loyalty of a target company (initially Xiaomi).

It ingests reports (PDF, Markdown), analyzes them for information relevant to predefined brand loyalty metrics, assesses the significance and novelty of the findings against a local baseline report, and proposes updates for human review via a Streamlit interface.

## Features

*   **Document Ingestion:** Processes `.pdf` and `.md` files from an input directory.
*   **Text Chunking & Embedding:** Splits documents into manageable chunks and generates embeddings using OpenAI models (via `LLMInterface`).
*   **Vector Storage:** Stores document chunks and embeddings in a local ChromaDB vector store.
*   **Retrieval-Augmented Generation (RAG):**
    *   Retrieves relevant document chunks based on predefined brand loyalty metrics.
    *   Compares retrieved information against the current section in the baseline report.
    *   Uses an LLM (e.g., `gpt-o4-mini`) to assess the significance of new information.
    *   Generates concise update paragraphs only for significant findings, citing sources.
*   **Local Report Management:** Assumes the baseline report (`data/core_files/baseline_report.md`) is managed locally.
*   **Review UI:** Provides a Streamlit interface to:
    *   Trigger the analysis pipeline.
    *   Display proposed updates alongside their sources.
    *   Allow human reviewers to "Approve" or "Reject" updates.
    *   Update the local `baseline_report.md` directly upon approval.

## Technology Stack

*   **Language:** Python 3.12
*   **LLM Interaction:** OpenAI API (via custom `LLMInterface`)
*   **Embedding Model:** OpenAI `text-embedding-ada-002` (or configurable via `.env`)
*   **LLM Model:** OpenAI `gpt-o4-mini` (or configurable via `.env`)
*   **Vector Database:** ChromaDB (local persistent storage)
*   **PDF Parsing:** `pdfplumber`
*   **Tokenization:** `tiktoken`
*   **Web UI:** Streamlit
*   **Dependencies:** `python-dotenv`, `pytest`, `pytest-mock`, `markdown-it-py`

(See `tech_stack.md` for more details)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Susan2025lee/brandloyaltyupdater.git
    cd brandloyaltyupdater
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate # Or equivalent for your shell (e.g., .venv\Scripts\activate on Windows)
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    *   Copy `.env.example` to `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Edit `.env` and provide your actual `OPENAI_API_KEY`. You can also adjust `DEFAULT_LLM_MODEL_KEY` and `DEFAULT_EMBEDDING_MODEL_KEY` if desired.
    *   **Important:** Ensure the `.env` file is NOT committed to Git (it should be in `.gitignore`).

5.  **Prepare Data Files:**
    *   Ensure the metric definitions file exists at `data/core_files/brandloyalty.md` (metrics should be in the first column of a Markdown table, like `| **Metric Name** | ... |`).
    *   Ensure the baseline report exists at `data/core_files/baseline_report.md`. Headings for metrics in this report should match the format `### A. Metric Name` (where `A` is the letter prefix).
    *   Place new input documents (PDF or Markdown) into the `data/input/` directory.

## Usage

1.  **Ensure Setup is Complete:** Verify all steps in the Setup section are done.
2.  **Run the Streamlit Application:**
    *   Open your terminal in the project root directory (`brandloyaltyupdater`).
    *   Make sure your virtual environment is activated.
    *   Run the command:
        ```bash
        streamlit run streamlit_app/app.py
        ```
3.  **Interact with the UI:**
    *   The application will open in your web browser.
    *   Click the **"Run Pipeline to Find Updates"** button. This will:
        *   Scan `data/input/` for new documents.
        *   Ingest, chunk, embed, and index the documents into ChromaDB.
        *   Compare new information against `data/core_files/baseline_report.md` for each metric defined in `data/core_files/brandloyalty.md`.
        *   Generate proposed updates if significant new information is found.
    *   Review the **Proposed Updates** displayed.
    *   For each update:
        *   Click **"Approve"** to accept the change. This will attempt to automatically update the corresponding section in the local `data/core_files/baseline_report.md` file.
        *   Click **"Reject"** to discard the proposed change.
    *   Check the **Actioned Updates Summary** to see the status of reviews.
    *   Verify changes by manually inspecting the `data/core_files/baseline_report.md` file after approving updates.

## Project Structure

```
brandloyaltyupdater/
├── .env            # Local environment variables (API Keys, etc.) - DO NOT COMMIT
├── .env.example    # Example environment file
├── .gitignore      # Specifies intentionally untracked files that Git should ignore
├── README.md       # This file
├── config.json     # Model configuration (Optional, based on LLMInterface usage)
├── requirements.txt # Project dependencies
├── data/
│   ├── core_files/ # Core definition files
│   │   ├── brandloyalty.md      # Defines metrics to track
│   │   └── baseline_report.md   # The main report being monitored/updated
│   ├── input/        # Place new input documents (PDF, MD) here
│   ├── processed/    # (Optional: Could be used for processed file tracking)
│   └── vector_store/ # Local ChromaDB persistent storage
├── implementation_plan.md # Development plan overview
├── prd.md               # Product Requirements Document
├── scripts/             # Helper scripts (e.g., run_pipeline.sh for cron)
├── src/
│   ├── core/            # Core utilities (e.g., LLM Interface)
│   │   └── llm_interface.py
│   ├── __init__.py
│   ├── config.py        # Loads configuration from .env
│   ├── embed.py         # Handles text embedding generation
│   ├── generate.py      # Handles LLM generation (assessment, summaries)
│   ├── ingest.py        # Handles document scanning, parsing, chunking
│   ├── main.py          # Main pipeline orchestration script
│   ├── models.py        # Pydantic models (e.g., DocumentChunk)
│   ├── prompts.py       # Stores LLM prompt templates
│   ├── report_parser.py # Parses and updates the baseline report
│   ├── retrieve.py      # Handles retrieval from vector store
│   └── vector_store.py  # Manages interaction with ChromaDB
├── streamlit_app/
│   └── app.py         # Streamlit review application
├── tasklist.md          # Detailed task breakdown
├── tech_stack.md        # Technology stack choices
└── tests/               # Unit and integration tests
    ├── fixtures/        # Test fixtures/data
    ├── __init__.py
    └── test_*.py        # Pytest test files
```

## Future Considerations / Notes

*   **Error Handling:** Error handling in `src/main.py` and other modules could be more robust.
*   **Input File Management:** Currently, all files in `data/input/` are processed every time. A mechanism to track already processed files could improve efficiency.
*   **Source Attribution:** Source attribution in `src/main.py` currently just takes the source of the first retrieved chunk. More sophisticated aggregation might be desired.
*   **Configuration:** Some hardcoded values (like `retrieval_k` in `main.py`) could be moved to `config.py`.
*   **Deployment:** The `scripts/run_pipeline.sh` and cron job setup (Tasks 4.10, 4.11) are not yet implemented.
*   **Testing:** More comprehensive integration and end-to-end tests could be added. 