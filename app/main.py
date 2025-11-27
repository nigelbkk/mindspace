import chromadb
from app.config import settings
from fastapi import FastAPI
from .routers import memory, health
from .config import settings
from .embeddings import embed_text
from . import db
import json

app = FastAPI(title="MindSpace Memory Service")
app.include_router(memory.router, prefix="/memory", tags=["Memory"])
app.include_router(health.router, prefix="/health", tags=["Health"])

# Init Chroma collection
chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
collection = chroma_client.get_or_create_collection(
    name=settings.COLLECTION_NAME
)

with open("data/static_profile.json") as f:
    STATIC_PROFILE = json.load(f)

@app.post("/memory/context")
async def get_context(payload: dict):
    context = f"[CONTEXT]\nLocation: {STATIC_PROFILE}\n"
    # context = f"[CONTEXT]\nLocation: {STATIC_PROFILE['location']}\n"
    # ... add structured facts, semantic results
    return {"context": context}

# Routers
# app.include_router(memory.router, prefix="/memory", tags=["Memory"])
# app.include_router(health.router, prefix="/health", tags=["Health"])
