## Implementation Plan - Brand Loyalty Monitor PoC

This plan outlines the key stages for developing the Proof of Concept (PoC).

### Stage 1: Core Ingestion & Processing Setup (Foundation)

*   **Goal:** Set up the project structure, basic file handling, chunking, and embedding.
*   **Tasks:**
    *   Initialize Git repository and project structure.
    *   Implement basic configuration management (e.g., `.env` for API keys).
    *   Develop script (`ingest.py`) to:
        *   Scan input directory for new `.md` and `.pdf` files.
        *   Extract text content using appropriate libraries (`pdfplumber`).
        *   Implement chunking logic using `tiktoken` targeting ~500 tokens.
        *   Add basic metadata to chunks (source filename, chunk ID).
    *   Develop script/module (`embed.py`) to:
        *   Wrap OpenAI API calls for generating embeddings (`text-embedding-ada-002`) using `LLMInterface`.
        *   Handle batching and potential API errors.
    *   Set up local ChromaDB instance (`vector_store.py`).
    *   Create script (`index_data.py`) to embed chunks and store them in ChromaDB.
*   **Testing:** Unit tests for text extraction, chunking logic, and ChromaDB interaction (add/query simple data).
*   **Outcome:** Ability to ingest sample documents, chunk them, generate embeddings, and store/retrieve them from a local vector store.

### Stage 2: Retrieval & Generation Core (RAG Pipeline)

*   **Goal:** Implement the core RAG logic to retrieve relevant information and generate initial update summaries.
*   **Tasks:**
    *   Develop retrieval function (`retrieve.py`) to query ChromaDB based on input queries (e.g., brand loyalty metric descriptions).
    *   Draft initial LLM prompts (`prompts.py`) for generating update summaries based *only* on retrieved context (without significance check yet).
    *   Implement generation function (`generate.py`) to:
        *   Take retrieved context and a metric description.
        *   Call the LLM (e.g., `gpt-o4-mini`) using `LLMInterface` with the summarization prompt.
        *   Include source citation in the generated output.
*   **Testing:** Unit tests for retrieval function (mocking ChromaDB results). Test generation function with sample context and prompts. Integration test connecting retrieval and generation.
*   **Outcome:** Ability to query for information related to a metric, retrieve relevant chunks, and generate a basic summary paragraph citing sources.

### Stage 3: Significance Assessment & Refined Generation

*   **Goal:** Introduce the crucial logic for assessing novelty/significance and refine the generation process.
*   **Tasks:**
    *   Develop function (`report_parser.py`) to parse the current `data/core_files/baseline_report.md` (e.g., using regex or Markdown parsing) to extract the existing text for specific metric sections.
    *   Refine LLM prompts (`prompts.py`) or create new ones specifically for the significance assessment and update generation step. This prompt needs to instruct the LLM to:
        1.  Consider the *retrieved context* from the new document.
        2.  Consider the *current text* for the relevant metric from the baseline report.
        3.  Determine if the new context provides *significant and novel* information compared to the baseline.
        4.  If yes, generate an *updated paragraph* incorporating the new insight and citing the source.
        5.  If no, output a specific indicator (e.g., `NO_UPDATE_NEEDED`).
    *   Update the generation function (`generate.py`) to use the new prompts and handle the conditional output.
*   **Testing:** Test the report parser. Test the refined generation logic with various scenarios (novel info, redundant info, slightly different info). Extensive prompt testing and refinement will be key here.
*   **Outcome:** Ability to generate update paragraphs *only* when new, significant information is found, comparing against the current report state.

### Stage 4: Integration, UI, and Orchestration

*   **Goal:** Connect all components, build the review UI, implement report updates, and set up basic orchestration.
*   **Tasks:**
    *   Develop main script (`main.py` or `run_pipeline.py`) to orchestrate the flow: load local report -> ingest -> embed -> index -> retrieve -> assess/generate -> store updates for UI.
    *   Build Streamlit application (`app.py`) to:
        *   Display proposed updates (generated text + source).
        *   Provide 'Approve' / 'Reject' buttons.
        *   On 'Approve', trigger the update of the local `data/core_files/baseline_report.md` (or alternative mechanism).
    *   Set up simple orchestration (e.g., a shell script run by Cron) to execute the main pipeline script periodically.
*   **Testing:** Integration tests for the full pipeline. Test the Streamlit UI functionality. Test the local report update process.
*   **Outcome:** A functional PoC system that processes new documents, proposes significant updates via a UI, and updates the master report (`data/core_files/baseline_report.md`) locally upon approval. 