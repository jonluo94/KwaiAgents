import os

# CHROMA POSTGRES
MEMORY_TYPE = os.environ.get("MEMORY_TYPE", "CHROMA")

CHROMADB_STORAGE_PATH = os.environ.get("CHROMADB_STORAGE_PATH", "chromadb")

POSTGRES_CONNECTION_STRING = os.environ.get("POSTGRES_CONNECTION_STRING",
                                            "postgres://postgres:memory2024@localhost:5432/postgres")
