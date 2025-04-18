import os
from dotenv import load_dotenv
from pathlib import Path

# Determine the project root directory
# Assumes config.py is in src/, so two levels up is the project root
project_root = Path(__file__).resolve().parent.parent

# Load the .env file from the project root
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

# --- Load configuration values --- 

# LLM Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_LLM_MODEL_KEY = os.getenv("DEFAULT_LLM_MODEL_KEY", "gpt-o4-mini") # Default fallback
USE_LLM_PROXY_STR = os.getenv('USE_LLM_PROXY', 'True').lower()
USE_LLM_PROXY = USE_LLM_PROXY_STR == 'true'
MODEL_CONFIG_PATH = os.getenv("MODEL_CONFIG_PATH") # Will be None if not set
DEFAULT_EMBEDDING_MODEL_KEY = os.getenv("DEFAULT_EMBEDDING_MODEL_KEY", "text-embedding-ada-002") # Default fallback

# GitHub Configuration (Optional - for Phase 4)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")

# --- Define File Paths (relative to project root) --- 

DATA_DIR = project_root / "data"
CORE_FILES_DIR = DATA_DIR / "core_files"
INPUT_DIR = DATA_DIR / "input"
PROCESSED_DIR = DATA_DIR / "processed"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

BASELINE_REPORT_PATH = CORE_FILES_DIR / "baseline_report.md"
BRAND_LOYALTY_METRICS_PATH = CORE_FILES_DIR / "brandloyalty.md"

# --- Validation (Optional but recommended) --- 

if not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY environment variable not set.")
    # Depending on the use case, you might want to raise an error here
    # raise ValueError("OPENAI_API_KEY must be set in the .env file")

print(f"Configuration loaded:")
print(f"- DEFAULT_LLM_MODEL_KEY: {DEFAULT_LLM_MODEL_KEY}")
print(f"- DEFAULT_EMBEDDING_MODEL_KEY: {DEFAULT_EMBEDDING_MODEL_KEY}")
print(f"- USE_LLM_PROXY: {USE_LLM_PROXY}")
print(f"- BASELINE_REPORT_PATH: {BASELINE_REPORT_PATH}") 