import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = BASE_DIR / "knowledge_base"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = "claude-sonnet-4-20250514"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
TOP_K = 3

CHROMA_DIR = str(DATA_DIR / "chroma_db")
SQLITE_PATH = str(DATA_DIR / "app.db")
