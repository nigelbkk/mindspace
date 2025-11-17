import os

class Settings:
    SQLITE_PATH = os.getenv("SQLITE_PATH", "data/memories.sqlite3")
    CHROMA_PATH = os.getenv("CHROMA_PATH", "data/chroma")
    OLLAMA_EMBED_MODEL = os.getenv("EMBED_MODEL", "nomic-embed-text")
    COLLECTION_NAME = "mindspace_memories"

settings = Settings()
