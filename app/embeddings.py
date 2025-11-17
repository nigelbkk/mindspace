import requests
from .config import settings

def embed_text(text: str):
    payload = {"model": settings.OLLAMA_EMBED_MODEL, "prompt": text}
    r = requests.post("http://localhost:11434/api/embeddings", json=payload)
    r.raise_for_status()
    return r.json()["embedding"]
