import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

APP_DIR = Path(__file__).resolve().parent
load_dotenv(APP_DIR / ".env") 

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data"
VECTOR_STORE_DIR = BASE_DIR / "vector_store" / "chroma"
EMBEDDING_MODEL_NAME = "gemini-embedding-001"

GCP_PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
GCP_REGION = os.getenv("GCP_REGION", "us-central1")
