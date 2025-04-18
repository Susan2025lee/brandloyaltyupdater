## Product Requirements Document (PRD) - Brand Loyalty Monitor PoC

### 1. Objectives

*   **Automate Insight Extraction:** Extract potentially relevant information regarding predefined brand loyalty metrics from incoming documents (Markdown, PDF).
*   **Assess Significance & Novelty:** Evaluate extracted information against the current baseline report to determine if it represents a genuinely new and meaningful insight, filtering out redundant or trivial updates.
*   **Generate Update Summaries:** For significant and novel insights, generate concise, coherent update paragraphs contextualized for the specific brand loyalty metric. Summaries must cite the source document.
*   **Maintain Living Report:** Integrate approved update paragraphs into a master Markdown report (`data/core_files/baseline_report.md`), tracking changes using version control (GitHub).
*   **Facilitate Review:** Provide a simple User Interface (UI) for human review and approval/rejection of proposed updates before they are merged into the master report.

### 2. Scope (Proof of Concept)

*   **Input:** Ingestion of new reports (Markdown `.md`, PDF `.pdf`) placed in a designated input directory.
*   **Processing:**
    *   Document parsing and text extraction.
    *   Chunking documents into manageable passages (approx. 500 tokens).
    *   Generating embeddings for text chunks.
    *   Storing and indexing chunks and embeddings in a local vector database.
    *   Retrieving relevant chunks based on brand loyalty metrics and context from the current report.
    *   Utilizing a Large Language Model (LLM) via Retrieval-Augmented Generation (RAG) to:
        1.  Compare retrieved information against the current report section for a given metric.
        2.  Assess novelty and significance based on predefined criteria (potentially embedded in the prompt or as a separate step).
        3.  Generate a draft update paragraph *only if* the information is deemed significant and novel.
        4.  Ensure source attribution in the generated paragraph.
*   **Output:** Proposed update paragraphs displayed in a review UI. Approved updates are automatically committed to the `data/core_files/baseline_report.md` on GitHub.
*   **Metrics:** Focus on the brand loyalty metrics defined in `data/core_files/brandloyalty.md`.
*   **Target Company:** Initial focus on Xiaomi, using the initial version of `data/core_files/baseline_report.md`.
*   **Technology:** Utilize the specific PoC tech stack defined in `tech_stack.md`.
*   **Orchestration:** Simple sequential execution via Python scripts, potentially triggered by a cron job.

### 3. Out of Scope (PoC)

*   Real-time processing.
*   Complex orchestration or distributed systems.
*   Advanced UI features beyond simple review/approval.
*   Automated credibility assessment of sources.
*   Handling diverse input formats beyond Markdown and PDF.
*   Automatic score adjustments (updates will focus on justification text; score changes require manual review).

### 4. Success Criteria

*   **End-to-End Flow:** The system successfully ingests, processes, and proposes updates for at least one new input report against the baseline report.
*   **Meaningful Updates:** Generates relevant, novel, and significant update paragraphs (as judged by a human reviewer) for at least two different brand loyalty metrics.
*   **Review UI:** The Streamlit UI correctly loads and displays proposed updates, allowing for human approval/rejection.
*   **Version Control:** Approved updates are successfully committed to the `data/core_files/baseline_report.md` file on GitHub.
*   **Performance:** The end-to-end pipeline for processing 10 typical input reports completes within a reasonable timeframe (e.g., < 15 minutes) for PoC purposes. 