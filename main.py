"""
main.py
--------
FastAPI application exposing the RAG pipeline as a web service:

  GET  /              -> serves the chat UI (templates/index.html)
  POST /api/ingest     -> upload PDF(s), ingest into Pinecone
  POST /api/ask         -> ask a question, get a generated answer + sources
  GET  /api/health      -> simple health check (useful for Azure)

Run locally:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Run in Docker (see Dockerfile):
    uvicorn main:app --host 0.0.0.0 --port 8000
"""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from pipeline import RAGPipeline

app = FastAPI(title="RAG Pipeline with Pinecone")

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "data"
UPLOAD_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# The pipeline connects to Pinecone + loads the embedding model on startup.
# Keeping this as a module-level singleton avoids reloading the model
# on every request.
rag_pipeline: RAGPipeline | None = None


@app.on_event("startup")
def load_pipeline():
    global rag_pipeline
    rag_pipeline = RAGPipeline()


class AskRequest(BaseModel):
    question: str
    top_k: int | None = None


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/ingest")
async def ingest(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    saved_paths = []
    for upload in files:
        if not upload.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail=f"Only PDF files are supported: {upload.filename}"
            )
        dest = UPLOAD_DIR / upload.filename
        with dest.open("wb") as f:
            shutil.copyfileobj(upload.file, f)
        saved_paths.append(str(dest))

    total_chunks = 0
    for path in saved_paths:
        total_chunks += rag_pipeline.ingest(path)

    return {
        "message": f"Ingested {len(saved_paths)} file(s) successfully",
        "files": [os.path.basename(p) for p in saved_paths],
        "chunks_indexed": total_chunks,
    }


@app.post("/api/ask")
def ask(payload: AskRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = rag_pipeline.ask(payload.question, top_k=payload.top_k)
    return result
