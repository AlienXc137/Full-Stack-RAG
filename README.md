# Full-Stack RAG Document Portal (FastAPI)
A Retrieval-Augmented Generation (RAG) application built with LangChain, FastAPI, and Google Gemini / Groq LLMs, designed for multi-document intelligent chat.
The system allows users to upload PDFs, DOCX, or TXT files, automatically index them using FAISS embeddings, and chat with the ingested knowledge — all deployed on AWS ECS Fargate with a full CI/CD pipeline.

## Features
- Multi-document ingestion with FAISS vector store  
- RAG pipeline with Google Generative AI and Groq LLMs  
- Conversational memory and context aware responses  
- LangChain-powered retrievers and prompt templates  
- Structured logging and custom exception handling  
- Automated unit tests using pytest and CI workflows  
- Dockerized FastAPI backend  
- CI/CD to AWS ECS Fargate via GitHub Actions  
- Interactive web interface with file uploads and chat 

## Architecture Overview

```mermaid
  A[User Uploads Documents] --> B[FastAPI Backend]
  B --> C[Data Ingestion: Text Extraction + Chunking]
  C --> D[FAISS Vector Store]
  D --> E[Retriever]
  E --> F[LangChain RAG Pipeline]
  F --> G[LLM (Google Gemini / Groq)]
  G --> H[Response Streamed to UI]
  B --> I[Logging & Monitoring (Structlog + LangSmith)]
```

## How it works
- Upload: Files are uploaded to `data/<session_id>/`, split, embedded, and saved as a FAISS index in `faiss_index/<session_id>/`.
- Chat: Each request loads the FAISS index for the given `session_id` and answers using RAG.
- Sessions: A simple in-memory history per session on the server (resets on restart). The browser stores `session_id` in `localStorage`.

## Run locally
1. Install deps
```bash
pip install -r requirements.txt
```
2. Start the server
```bash
uvicorn main:app --reload
```
3. Open the UI
```bash
open http://localhost:8000/
```

## Endpoints
- `GET /` – Serves the UI.
- `GET /health` – Health check.
- `POST /upload` – Form-data file upload. Returns `{ session_id, indexed }`.
- `POST /chat` – JSON body `{ session_id, message }`. Returns `{ answer }`.

## Evaluations 

Run LangSmith evaluations on your RAG system:

```bash
# Quick start - run with default settings
python run_evaluations.py

# Run with all evaluators
python run_evaluations.py --evaluator all

# Custom parameters
python run_evaluations.py --evaluator correctness --chunk-size 500 --k 10
```

**Available Evaluators:**
- `correctness` - Custom LLM-as-a-Judge (Gemini 2.5 Pro)
- `cot_qa` - Chain-of-Thought QA evaluator
- `all` - Run all evaluators

## Notes
- Ensure your API keys/config are set for the `ModelLoader` to load embeddings/LLM.
- For evaluations, you need `LANGSMITH_API_KEY` and `GOOGLE_API_KEY` in your `.env` file.
- Supported file types: `.pdf`, `.docx`, `.txt`.
- For production, add persistence for chat history and auth; consider cleanup of old session directories.