import os

MEMORY_TYPE = os.environ.get("MEMORY_TYPE", "CHROMA")

CHROMADB_STORAGE_PATH = os.environ.get("CHROMADB_STORAGE_PATH", "chromadb")

POSTGRES_CONNECTION_STRING = os.environ.get("POSTGRES_CONNECTION_STRING", "postgres://postgres:memory2024@localhost:6543/memory")

POSTGRES_EMBEDDING_WIDTH = os.environ.get("POSTGRES_EMBEDDING_WIDTH", 512)
