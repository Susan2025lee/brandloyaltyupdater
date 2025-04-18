## Proposed File Structure

```plaintext
brand_loyalty_monitor/
├── .env                  # Environment variables (API keys, paths) - DO NOT COMMIT
├── .gitignore            # Git ignore rules
├── requirements.txt      # Python dependencies
├── prd.md                # Product Requirements Document
├── tech_stack.md         # Technology Stack definition
├── implementation_plan.md # Implementation Plan
├── file_structure.md     # Proposed File Structure (this file)
├── tasklist.md           # Detailed Task List
|
├── data/
│   ├── core_files/       # Directory for essential baseline/definition files
│   │   ├── baseline_report.md    # The master, living report (initially copy of xiaomi report)
│   │   └── brandloyalty.md       # Definition of loyalty metrics (reference)
│   ├── input/            # Directory for dropping new reports (.md, .pdf)
│   ├── processed/        # Directory for storing processed file info/metadata (optional)
│   └── vector_store/     # ChromaDB persistent storage directory
│
├── src/
│   ├── __init__.py
│   ├── config.py         # Load configuration from .env
│   ├── ingest.py         # Document loading, parsing, and chunking
│   ├── embed.py          # Embedding generation logic
│   ├── vector_store.py   # ChromaDB interaction wrapper
│   ├── index_data.py     # Script to run ingestion, embedding, indexing
│   ├── retrieve.py       # Retrieval logic from vector store
│   ├── prompts.py        # LLM prompt templates
│   ├── report_parser.py  # Logic to parse baseline_report.md
│   ├── generate.py       # Significance assessment and text generation logic
│   ├── github_utils.py   # GitHub interaction (fetch report, commit updates)
│   └── utils.py          # Common utility functions
│
├── scripts/
│   ├── run_pipeline.sh   # Example shell script for orchestration (run by cron)
│   └── run_indexing.sh   # Script to manually trigger indexing
│
├── streamlit_app/
│   └── app.py            # Streamlit UI application code
│
├── tests/
│   ├── __init__.py
│   ├── fixtures/         # Test data (sample docs, expected outputs)
│   ├── test_ingest.py
│   ├── test_embed.py
│   ├── test_vector_store.py
│   ├── test_retrieve.py
│   ├── test_report_parser.py
│   ├── test_generate.py
│   └── test_integration.py # End-to-end pipeline tests (subset)
│
└── README.md             # Project overview, setup, and usage instructions

```

**Notes:**

*   The `data/core_files/baseline_report.md` will be the core document that gets updated.
*   `data/vector_store/` should be added to `.gitignore` if not committing the DB.
*   `src/` contains the core Python modules for the pipeline.
*   `scripts/` contains helper scripts for running parts of the process.
*   `streamlit_app/` houses the UI code.
*   `tests/` contains all unit and integration tests, mirroring the `src` structure where appropriate. 