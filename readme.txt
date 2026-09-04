# RAG Pipeline — FastAPI + Docker (Azure-ready)

This is the web-service version of the RAG pipeline: same retrieval +
generation core (Pinecone, sentence-transformers, Groq for LLM answers),
now wrapped in a FastAPI app with a browser UI, ready to containerize
and deploy to Azure.

```
rag_pipeline_fastapi/
├── main.py                  # FastAPI app: serves UI + /api/ingest + /api/ask
├── pipeline.py               # Same RAG orchestration as the CLI version
├── config.py                 # Settings (.env)
├── Dockerfile                 # Container build for Azure deployment
├── .dockerignore
├── templates/
│   └── index.html            # Chat UI (upload PDFs, ask questions)
├── static/                    # Static assets (CSS/JS if split out later)
├── loaders/ splitters/ embeddings/ vectorstores/ generators/
│                              # Same modules as the CLI project
└── requirements.txt
```

## 1. Run locally (no Docker)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in PINECONE_API_KEY and GROQ_API_KEY
uvicorn main:app --reload
```

Open **http://localhost:8000** in a browser. You'll see:
1. An upload area — drop in a PDF, click **Ingest into archive**
2. A chat box below — ask a question, get a generated answer with source citations

Behind the scenes this calls the same `pipeline.ingest()` and
`pipeline.ask()` methods as the CLI version — the FastAPI layer is just
a thin HTTP wrapper (`/api/ingest`, `/api/ask`) around them.

## 2. Run with Docker

Build the image:
```bash
docker build -t rag-pipeline .
```

Run it (pass your Pinecone key as an env var, don't bake it into the image):
```bash
docker run -p 8000:8000 --env-file .env rag-pipeline
```

Open **http://localhost:8000**.

**Note on Groq**: Groq hosts the Llama model on its own inference
servers — your container just makes an API call with your
`GROQ_API_KEY`, the same way it already calls Pinecone. This means
there's no local model to download, no GPU/RAM requirement on the
container, and no extra networking setup needed for Docker or Azure —
the container just needs outbound internet access to reach
`api.groq.com`, which Azure Container Apps / App Service / Container
Instances all support by default.

## 3. Deploying to Azure

A few directions your sir may go, all compatible with this Dockerfile as-is:
- **Azure Container Apps** — push the image to Azure Container Registry,
  deploy as a Container App, set `PINECONE_API_KEY` etc. as secrets/env vars
- **Azure App Service (Web App for Containers)** — same image, deployed
  as a single container behind App Service
- **Azure Container Instances** — simplest option for a quick demo deployment

In all cases: the Dockerfile already reads the `$PORT` environment
variable (Azure sets this automatically for App Service), so no code
changes should be needed — just build, push to ACR, and point the
Azure service at the image.

## 4. API reference

| Method | Path | Body | Description |
|---|---|---|---|
| GET | `/` | — | Serves the chat UI |
| GET | `/api/health` | — | Health check (useful for Azure probes) |
| POST | `/api/ingest` | multipart form, field `files` (PDFs) | Ingests PDF(s) into Pinecone |
| POST | `/api/ask` | `{"question": "...", "top_k": 4}` | Returns `{"answer": ..., "sources": [...]}` |

## Notes

- The embedding model and Pinecone connection load once at startup
  (`@app.on_event("startup")`), not per-request, so the first request
  after boot may be slightly slower while the model warms up.
- CORS isn't configured yet — fine for same-origin (UI served by the
  same FastAPI app), but if the UI is ever split onto a different
  domain, add `fastapi.middleware.cors.CORSMiddleware`.
