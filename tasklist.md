## Task List - Brand Loyalty Monitor PoC

This task list breaks down the implementation plan into actionable items, including testing.

### Phase 0: Project Setup & Configuration

*   [x] Task 0.1: Initialize Git repository on GitHub.
*   [x] Task 0.2: Set up local project structure according to `file_structure.md`.
*   [x] Task 0.3: Create initial `requirements.txt` with known base dependencies (python-dotenv, pytest, etc.).
*   [x] Task 0.4: Create `.gitignore` file (include `.env`, `data/vector_store/`, `__pycache__/`, etc.). Add `config.json`.
*   [x] Task 0.5: Set up `.env` file template (`.env.example`) and `src/config.py` to load environment variables (API Keys, file paths). Add `DEFAULT_LLM_MODEL_KEY` and `DEFAULT_EMBEDDING_MODEL_KEY` to `.env.example`.
*   [x] Task 0.5: Set up `.env` file template (`.env.example`) and `src/config.py` to load environment variables (API Keys, file paths). Add `DEFAULT_LLM_MODEL_KEY` to `.env.example`.
*   [x] Task 0.6: Set up `pytest` framework, including basic configuration (`pytest.ini` if needed).
*   [x] Task 0.7: Create `tests/fixtures/` directory and add initial sample input files (.md, .pdf) and copy `data/core_files/brandloyalty.md` to fixtures for reference in tests.
*   [x] Task 0.8: Copy `xiaomi_brandloyalty_gemini2.5.md` to `data/core_files/baseline_report.md` (Placeholder created).
*   [x] Task (Implicit): Create `README.md`.
*   [x] Task (Implicit): Create virtual environment and install dependencies.
*   [x] Task (Implicit): Initial Git commit and push.

### Phase 1: Core Ingestion & Processing Setup

*   **Module: `src/ingest.py`**
    *   [x] Task 1.1: Implement function to scan `data/input/` directory for `.md` and `.pdf` files.
    *   [x] Task 1.2: Implement PDF text extraction using `pdfplumber`.
        *   [x] *Test 1.2.1:* Unit test PDF extraction with sample PDF (`tests/test_ingest.py`).
    *   [x] Task 1.3: Implement Markdown text extraction (basic file read for PoC).
        *   [x] *Test 1.3.1:* Unit test MD extraction with sample MD (`tests/test_ingest.py`).
    *   [x] Task 1.4: Implement chunking logic using `tiktoken`.
        *   [x] *Test 1.4.1:* Unit test chunking logic for various text lengths and edge cases (`tests/test_ingest.py`).
    *   [x] Task 1.5: Add metadata (source filename, chunk ID) to each chunk (via `ingest_documents`).
        *   [x] *Test 1.5.1:* Verify metadata presence and correctness in chunking unit tests (`tests/test_ingest.py`).
*   **Module: `src/embed.py`**
    *   [x] Task 1.6: Implement wrapper function for OpenAI embedding API calls **using `LLMInterface`**.
    *   [x] Task 1.7: Handle potential API errors and retries (simple implementation for PoC - handled in LLMInterface).
    *   [x] Task 1.8: Implement batching for embedding requests (if handling multiple chunks - basic list handling implemented, complex batching deferred).
        *   [x] *Test 1.6-8:* Unit test embedding wrapper using mocking (`tests/test_embed.py`).
*   **Module: `src/vector_store.py`**
    *   [x] Task 1.9: Implement ChromaDB client initialization (persistent, using `data/vector_store/`).
    *   [x] Task 1.10: Implement function to add embedded chunks (with metadata) to ChromaDB collection.
    *   [x] Task 1.11: Implement basic query function (placeholder for Stage 2 - basic query implemented).
        *   [x] *Test 1.9-11:* Unit test ChromaDB interactions (add, count, basic query) using a temporary test database (`tests/test_vector_store.py` with mocks).
*   **Script: `src/index_data.py`**
    *   [x] Task 1.12: Create script orchestrating ingest -> embed -> add to vector store.
    *   [x] *Test 1.12.1:* Manual run test with sample files to ensure data populates ChromaDB.

### Phase 2: Retrieval & Generation Core

*   **Module: `src/retrieve.py`**
    *   [x] Task 2.1: Implement function to take a query (e.g., metric description) and retrieve relevant chunks from ChromaDB.
    *   [x] Task 2.2: Define retrieval parameters (e.g., number of chunks `k`).
        *   [x] *Test 2.1-2:* Unit test retrieval function, mocking ChromaDB query results (`tests/test_retrieve.py`).
*   **Module: `src/prompts.py`**
    *   [x] Task 2.3: Draft initial basic summarization prompt template (input: context, metric; output: summary paragraph with citation).
    *   [x] Task 2.4: Refine/Create LLM prompt template for significance assessment and conditional generation (Input: retrieved context, current report context, metric; Output: update paragraph or `NO_UPDATE_NEEDED`).
    *   [x] Task 2.5: Iterate on prompt design based on testing.
*   **Module: `src/generate.py`**
    *   [x] Task 2.6: Implement function wrapping OpenAI LLM call for generation **using `LLMInterface`**.
    *   [x] Task 2.7: Implement logic to format context, metric, and prompt for the LLM.
    *   [x] Task 2.8: Implement basic source citation logic based on retrieved chunk metadata.
    *   [x] Task 2.9: Update generation function to fetch current report context using `report_parser`.
    *   [x] Task 2.10: Update generation function to use the new significance/conditional prompt.
    *   [x] Task 2.11: Handle the `NO_UPDATE_NEEDED` response.
        *   [x] *Test 2.6-11:* Unit test generation function using mocked LLM calls, verifying prompt formatting and output parsing (`tests/test_generate.py`).
*   **Integration:**
    *   [x] Task 2.12: Test the flow: retrieve chunks -> generate basic summary.
        *   [x] *Test 2.12.1:* Write simple integration test combining `retrieve` and `generate` (mocking DB and LLM) (`tests/test_integration.py`).

### Phase 3: Significance Assessment & Refined Generation

*   **Module: `src/report_parser.py`**
    *   [x] Task 3.1: Implement function to read `data/core_files/baseline_report.md`.
    *   [x] Task 3.2: Implement logic (e.g., regex or section markers) to extract text for a specific metric section (e.g., based on `## III.X Metric Name`).
        *   [x] *Test 3.1-2:* Unit test report parsing with sample baseline report content (`tests/test_report_parser.py`).
*   **Module: `src/prompts.py`**
    *   [x] Task 3.3: Refine/Create LLM prompt template for significance assessment and conditional generation (Input: retrieved context, current report context, metric; Output: update paragraph or `NO_UPDATE_NEEDED`).
    *   [x] Task 3.4: Iterate on prompt design based on testing.
*   **Module: `src/generate.py`**
    *   [x] Task 3.5: Update generation function to fetch current report context using `report_parser`.
    *   [x] Task 3.6: Update generation function to use the new significance/conditional prompt.
    *   [x] Task 3.7: Handle the `NO_UPDATE_NEEDED` response.
        *   [x] *Test 3.5-7:* Update unit tests for `generate` with mocked report context and test different LLM response scenarios (update needed, no update needed) (`tests/test_generate.py`).

### Phase 4: Integration, UI, and Orchestration

*   **Module: `streamlit_app/app.py`**
    *   [x] Task 4.4: Set up basic Streamlit app structure.
    *   [x] Task 4.5: Implement logic to display proposed updates (text + source).
    *   [x] Task 4.6: Add 'Approve' / 'Reject' buttons for each proposed update.
    *   [x] Task 4.7: Implement logic to update local `data/core_files/baseline_report.md` upon approval (or alternative mechanism).
        *   [x] *Test 4.4-7:* Manual testing of the Streamlit UI flow.
*   **Orchestration & Main Script:**
    *   [x] Task 4.8: Develop main script (`src/main.py` or similar) to orchestrate the full pipeline: Load local report -> Ingest new docs -> Index -> Retrieve -> Assess/Generate -> Store proposed updates (e.g., in memory or temp file for Streamlit).
    *   [ ] Task 4.9: Refine script to handle potential errors gracefully.
    *   [ ] Task 4.10: Create simple wrapper script (`scripts/run_pipeline.sh`) for cron execution.
    *   [ ] Task 4.11: Configure Cron job (manual step, outside codebase).
        *   [x] *Test 4.8-11:* End-to-end integration testing by running the pipeline script manually, reviewing output in Streamlit, approving, and checking local `data/core_files/baseline_report.md` update.

### Phase 5: Documentation & Finalization

*   [x] Task 5.1: Create `README.md` with project overview, setup instructions, and usage guide.
*   [x] Task 5.2: Add docstrings to all functions and classes.
*   [x] Task 5.3: Clean up code and ensure consistency.
*   [x] Task 5.4: Final review of all documents (`prd.md`, `tech_stack.md`, etc.).