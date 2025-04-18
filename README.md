# Brand Loyalty Monitor PoC

This project is a Proof of Concept (PoC) for an automated system to monitor the brand loyalty of a target company.

It ingests reports (PDF, Markdown), analyzes them for information relevant to predefined brand loyalty metrics, assesses the significance and novelty of the findings against a baseline report, and proposes updates for human review via a Streamlit interface.

## Project Structure

(See `file_structure.md` for details)

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Susan2025lee/brandloyaltyupdater.git
    cd brandloyaltyupdater
    ```
2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate # Or equivalent for your shell
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
    *   Edit `.env` and provide your actual values (especially `OPENAI_API_KEY` if not using `config.json`, `DEFAULT_LLM_MODEL_KEY`, `USE_LLM_PROXY`). **DO NOT COMMIT THE `.env` FILE.**
5.  **Configuration (`config.json`):**
    *   Ensure you have a `config.json` file (as specified by `model_manager.py` used within `LLMInterface`) containing necessary model details, including API keys. This file is ignored by Git.

## Usage

(Instructions to be added as development progresses)

*   Running the pipeline
*   Running the Streamlit review UI

## Key Documents

*   `prd.md`: Product Requirements Document
*   `tech_stack.md`: Technology Stack
*   `implementation_plan.md`: Implementation Plan
*   `tasklist.md`: Detailed Task List
*   `file_structure.md`: Project Directory Layout
*   `data/core_files/brandloyalty.md`: Definition of Brand Loyalty Metrics
*   `data/core_files/baseline_report.md`: The core report being updated 