# RAG-Based Quiz Generator

A Retrieval-Augmented Generation (RAG) application that generates multiple-choice quizzes from PDF documents using semantic search, local text embeddings, ChromaDB, and Google Gemini.

## Overview

The system retrieves relevant information from ingested PDF documents and uses that context to generate topic-specific quiz questions.

Instead of asking an LLM to generate questions from general knowledge alone, the RAG pipeline grounds quiz generation in the content retrieved from the document collection.

## Architecture

```text
             PDF Documents
                   |
                   v
             PDF Processing
                   |
                   v
          Text Chunking
          (1000 characters,
           200 overlap)
                   |
                   v
        HuggingFace Embeddings
          (all-MiniLM-L6-v2)
                   |
                   v
              ChromaDB
           Vector Database
                   |
                   |
User Topic --------+
                   |
                   v
            Semantic Retrieval
             (Top 3 Chunks)
                   |
                   v
             Retrieved Context
                   |
                   v
              Google Gemini
                   |
                   v
          Multiple-Choice Quiz
                (JSON)
```

## Features

- **Retrieval-Augmented Generation:** Uses retrieved document content to ground quiz generation.
- **PDF Ingestion:** Extracts and processes PDF documents for the knowledge base.
- **Local Embeddings:** Uses a HuggingFace sentence-transformer embedding model.
- **Vector Database:** Stores document embeddings in ChromaDB.
- **Semantic Retrieval:** Retrieves relevant document chunks based on a user's topic.
- **AI Quiz Generation:** Uses Google Gemini to generate multiple-choice questions.
- **REST API:** Provides a FastAPI backend for application integration.
- **API Smoke Checks:** Includes a script for manually checking API functionality.

## Technology Stack

| Component | Technology |
|---|---|
| Programming language | Python |
| API framework | FastAPI |
| LLM | Google Gemini |
| Embedding model | all-MiniLM-L6-v2 |
| Embedding framework | HuggingFace / Sentence Transformers |
| Vector database | ChromaDB |
| RAG framework | LangChain |
| PDF processing | PyPDF |
| Environment configuration | python-dotenv |

## Project Structure

```text
RAG_system/
│
├── src/
│   ├── __init__.py
│   ├── api.py                 # FastAPI application
│   ├── main.py                # Main application entry point
│   ├── ingest.py              # PDF ingestion functionality
│   ├── generator.py           # Quiz generation functionality
│   └── rag_engine.py          # RAG pipeline and retrieval logic
│
├── tests/
│   └── api_smoke_check.py     # Manual API smoke checks
│
├── pdfs/                      # PDF documents
├── chroma_db/                 # Local vector storage (if used)
│
├── .env                       # Local environment variables
├── .env.example               # Environment variable template
├── .gitignore
├── .dockerignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
└── README.md
```

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Surbi40/RAG_SYSTEM-Quiz.git
cd RAG_SYSTEM-Quiz
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.

Use `.env.example` as a reference:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get your API key from [Google AI Studio](https://aistudio.google.com/apikey).

**Security:** Never commit your actual `.env` file or expose your API key in source code, logs, screenshots, or Git history.

### 5. Start the API server

From the project root:

```powershell
uvicorn src.api:app --reload
```

The API server should be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## Testing

The project includes a manual API smoke-check script.

Make sure the API server is running in another terminal, then execute:

```powershell
python .\tests\api_smoke_check.py
```

The script checks API functionality, including health checks, topic retrieval, quiz generation, and document-related endpoints.

Some checks require a working Gemini API key and an accessible vector database.

## Configuration

### Environment Variables

| Variable | Description | Required |
|---|---|---|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |

### RAG Configuration

The current RAG implementation uses the following configuration:

| Parameter | Value |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` |
| Chunk size | 1000 characters |
| Chunk overlap | 200 characters |
| Retrieved chunks | 3 |
| Gemini temperature | 0.3 |
| Gemini model | `gemini-1.5-flash` |

These values can be adjusted in the RAG implementation.

## How the RAG Pipeline Works

1. **Document ingestion:** PDF documents are loaded and their text is extracted.
2. **Text chunking:** Extracted text is divided into smaller overlapping chunks.
3. **Embedding generation:** Each chunk is converted into a numerical vector using the HuggingFace embedding model.
4. **Vector storage:** The vectors and associated document content are stored in ChromaDB.
5. **User query:** A user submits a topic for quiz generation.
6. **Semantic retrieval:** The system retrieves the three most relevant document chunks.
7. **Quiz generation:** Retrieved context is passed to Google Gemini.
8. **Structured output:** The generated quiz is parsed into JSON.

## Future Improvements

- Improve quiz-generation output validation.
- Add authentication and authorization.
- Introduce more flexible retrieval and ranking strategies.
- Add automated unit and integration tests.
- Improve error handling and logging.
- Add configurable LLM and embedding models.
- Support additional document formats.
- Improve deployment and production configuration.
