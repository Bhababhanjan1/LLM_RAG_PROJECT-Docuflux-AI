"""
config.py
---------
Central configuration for the RAG pipeline.
All values can be overridden via environment variables so secrets
(API keys) never need to be hardcoded or committed to source control.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file if present
load_dotenv()


class Config:
    # ---------------- Pinecone ----------------
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-pipeline-index")
    PINECONE_CLOUD: str = os.getenv("PINECONE_CLOUD", "aws")
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "us-east-1")

    # ---------------- Embedding model ----------------
    # Any sentence-transformers model name works here.
    EMBEDDING_MODEL_NAME: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2"
    )
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))

    # ---------------- Text splitting ----------------
    CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))

    # ---------------- Retrieval ----------------
    TOP_K: int = int(os.getenv("TOP_K", "4"))

    # ---------------- Generation (Groq) ----------------
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # ---------------- Data ----------------
    DATA_DIR: str = os.getenv("DATA_DIR", "./data")

    @classmethod
    def validate(cls):
        """Fail fast with a clear message if required secrets are missing."""
        if not cls.PINECONE_API_KEY:
            raise ValueError(
                "PINECONE_API_KEY is not set. Add it to a .env file or "
                "export it as an environment variable."
            )
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to a .env file or "
                "export it as an environment variable."
            )


config = Config()
