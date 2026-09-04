# ---- RAG Pipeline (FastAPI) ----
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout (better logs on Azure)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# System deps needed by some ML wheels (torch/sentence-transformers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first (better layer caching on rebuilds)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# COPY . .
COPY main.py .
COPY config.py .
COPY pipeline.py .
COPY embeddings ./embeddings
COPY generators ./generators
COPY loaders ./loaders
COPY splitters ./splitters
COPY vectorstores ./vectorstores
COPY templates ./templates
COPY static ./static
COPY .env .

# Directory for uploaded PDFs (mount a volume here on Azure if you want persistence)
RUN mkdir -p /app/data

EXPOSE 8000

# Azure App Service / Container Apps sets $PORT; default to 8000 locally
ENV PORT=8000
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
