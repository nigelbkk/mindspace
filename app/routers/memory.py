from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import SessionLocal, Memory
from ..embeddings import embed_text
from ..config import settings
from ..models.schemas import MemoryCreate, RecallQuery
# from ..main import collection
from ..core import collection

import uuid
from datetime import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- REMEMBER ----------
@router.post("/remember")
def remember(mem: MemoryCreate, db: Session = Depends(get_db)):

    embedding = embed_text(mem.text)
    mem_id = str(uuid.uuid4())

    # Save metadata to SQLite
    db_entry = Memory(
        id=None,
        text=mem.text,
        type=mem.type,
        importance=mem.importance,
        tags=",".join(mem.tags)
    )
    db.add(db_entry)
    db.commit()
    db.refresh(db_entry)

    # Store in ChromaDB
    collection.add(
        ids=[str(db_entry.id)],
        documents=[mem.text],
        embeddings=[embedding],
        metadatas=[{"type": mem.type, "tags": mem.tags}]
    )

    return {"status": "saved", "id": db_entry.id}

# ---------- RECALL ----------
@router.post("/recall")
def recall(query: RecallQuery):
    q_emb = embed_text(query.query)

    results = collection.query(
        query_embeddings=[q_emb],
        n_results=query.k
    )

    # Return the best hits
    items = []
    for i in range(len(results["ids"][0])):
        items.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i]
        })

    return {"matches": items}
