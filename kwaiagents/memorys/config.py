import os

from .embedding import init_embedding

# CHROMA POSTGRES
MEMORY_TYPE = os.environ.get("MEMORY_TYPE", "POSTGRES")

CHROMADB_STORAGE_PATH = os.environ.get("CHROMADB_STORAGE_PATH", "chromadb")

POSTGRES_CONNECTION_STRING = os.environ.get("POSTGRES_CONNECTION_STRING",
                                            "postgres://postgres:memory2024@localhost:5432/postgres")

EMBEDDING_MODEL = init_embedding("BAAI/bge-m3")
