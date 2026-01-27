# Quiz Generator System - Complete Documentation

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Requirements](#3-requirements)
4. [Installation](#4-installation)
5. [API Reference](#5-api-reference)
6. [Backend Integration Guide](#6-backend-integration-guide)
7. [Frontend Integration Examples](#7-frontend-integration-examples)
8. [Configuration](#8-configuration)
9. [Deployment](#9-deployment)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. System Overview

### What is this?

The **Quiz Generator System** is a RAG (Retrieval-Augmented Generation) powered API that generates educational quizzes from PDF content. It's designed for the **Early Motherhood Support System** to create quizzes from health articles.

### Key Features

| Feature | Description |
|---------|-------------|
| **PDF Ingestion** | Upload PDFs to build the knowledge base |
| **AI Quiz Generation** | Generate multiple-choice quizzes on any topic |
| **Context-Aware** | Questions are based ONLY on your content |
| **Explanations** | Each answer includes educational explanations |
| **REST API** | Clean JSON endpoints for easy integration |
| **Docker Ready** | One-command deployment |

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Framework** | FastAPI | REST API server |
| **LLM** | Google Gemini 2.5 Flash | Quiz question generation |
| **Embeddings** | HuggingFace (all-MiniLM-L6-v2) | Local, free text embeddings |
| **Vector Database** | ChromaDB | Persistent document storage |
| **PDF Parser** | PyPDF | Extract text from PDFs |
| **Orchestration** | LangChain | RAG pipeline management |

---

## 2. Architecture

### RAG Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           QUIZ GENERATOR SYSTEM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────── INGESTION PHASE ────────────────────────────┐    │
│  │                                                                      │    │
│  │   [PDF File] ──► [PyPDF Loader] ──► [Text Splitter] ──► [Chunks]    │    │
│  │                                              │                       │    │
│  │                                              ▼                       │    │
│  │   [HuggingFace Embeddings] ◄── Convert to Vectors (LOCAL - FREE!)   │    │
│  │              │                                                       │    │
│  │              ▼                                                       │    │
│  │        [ChromaDB] ◄── Store Persistently (./chroma_db)              │    │
│  │                                                                      │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  ┌──────────────────────── GENERATION PHASE ───────────────────────────┐    │
│  │                                                                      │    │
│  │   [User Topic] ──► [Similarity Search] ──► [Relevant Chunks]        │    │
│  │                          │                        │                  │    │
│  │                          ▼                        ▼                  │    │
│  │                    [ChromaDB]              [Context Builder]         │    │
│  │                                                   │                  │    │
│  │                                                   ▼                  │    │
│  │   [Quiz JSON] ◄── [Google Gemini LLM] ◄── [Prompt + Context]        │    │
│  │                                                                      │    │
│  └──────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Cost Structure

| Component | Cost | Notes |
|-----------|------|-------|
| **Embeddings** | **FREE** | HuggingFace local model |
| **Vector Storage** | **FREE** | ChromaDB local storage |
| **Quiz Generation** | ~$0.001/quiz | Google Gemini API |

---

## 3. Requirements

### System Requirements

- **Python**: 3.10 or higher
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk**: 500MB for dependencies + space for PDFs
- **OS**: Windows, macOS, or Linux

### API Keys Required

| Service | Key Required | Free Tier |
|---------|-------------|-----------|
| **Google Gemini** | Yes | 15 requests/minute, 1500/day |
| **HuggingFace** | No | Unlimited (local) |

### Python Dependencies

```txt
# Core LangChain packages
langchain>=0.3.0
langchain-community>=0.3.0
langchain-core>=0.3.0

# Google Gemini for LLM (Quiz Generation)
langchain-google-genai>=2.0.0

# HuggingFace for local embeddings (FREE!)
langchain-huggingface>=0.1.0
sentence-transformers>=2.2.0

# Vector Database
chromadb>=0.5.0
langchain-chroma>=0.2.0

# PDF Processing
pypdf>=4.0.0

# API Server
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-multipart>=0.0.6

# Utilities
python-dotenv>=1.0.0
pydantic>=2.0.0
```

---

## 4. Installation

### Option A: Local Installation

```bash
# 1. Clone or navigate to the project
cd D:\RAG_system

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create .env file with your API key
echo GOOGLE_API_KEY=your_api_key_here > .env

# 6. Ingest a PDF (build knowledge base)
python main.py --ingest your_document.pdf

# 7. Start the API server
python api.py
```

### Option B: Docker Installation (Recommended for Production)

```bash
# 1. Create .env file with your API key
echo GOOGLE_API_KEY=your_api_key_here > .env

# 2. Build and start with Docker Compose
docker-compose up -d

# 3. Check logs
docker-compose logs -f

# 4. Stop the service
docker-compose down
```

### First-Time Setup (Ingest PDFs)

Before generating quizzes, you must ingest at least one PDF:

```bash
# Via CLI (local)
python main.py --ingest "./pdfs/maternal_health_guide.pdf"

# Via API (after server is running)
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@maternal_health_guide.pdf"
```

---

## 5. API Reference

### Base URL

```
Local:      http://localhost:8000
Production: https://your-domain.com
```

### Interactive Documentation

Once the server is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

### Endpoint: Health Check

**Check if the API is running and database is ready.**

```http
GET /api/health
```

#### Response

```json
{
  "status": "healthy",
  "database_ready": true,
  "message": "Ready to generate quizzes"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | `healthy` or `degraded` |
| `database_ready` | boolean | Whether knowledge base exists |
| `message` | string | Human-readable status |

---

### Endpoint: Generate Quiz

**Generate a quiz based on a topic.**

```http
POST /api/quiz/generate
Content-Type: application/json
```

#### Request Body

```json
{
  "topic": "postpartum depression",
  "num_questions": 5
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `topic` | string | Yes | - | Topic for quiz (2-200 chars) |
| `num_questions` | integer | No | 5 | Questions to generate (1-20) |

#### Success Response (200 OK)

```json
{
  "success": true,
  "topic": "postpartum depression",
  "questions": [
    {
      "id": 1,
      "question": "What is the primary screening tool for postpartum depression?",
      "options": [
        {
          "letter": "A",
          "text": "Edinburgh Postnatal Depression Scale (EPDS)",
          "is_correct": true
        },
        {
          "letter": "B",
          "text": "Beck Depression Inventory",
          "is_correct": false
        },
        {
          "letter": "C",
          "text": "Hamilton Rating Scale",
          "is_correct": false
        },
        {
          "letter": "D",
          "text": "PHQ-9",
          "is_correct": false
        }
      ],
      "correct_answer": "Edinburgh Postnatal Depression Scale (EPDS)",
      "explanation": "The EPDS is specifically designed for screening postpartum depression and is the most widely used tool in maternal mental health settings."
    }
  ],
  "total_questions": 5,
  "message": "Quiz generated successfully"
}
```

#### Error Responses

| Status | Reason | Response |
|--------|--------|----------|
| 503 | No database | `{"detail": "Knowledge base not initialized..."}` |
| 422 | Invalid input | `{"detail": [{"msg": "..."}]}` |
| 500 | Server error | `{"detail": "Internal server error..."}` |

---

### Endpoint: Get Suggested Topics

**Get topics that work well with the current knowledge base.**

```http
GET /api/topics
```

#### Response

```json
{
  "success": true,
  "topics": [
    {
      "topic": "Postpartum Depression",
      "relevance": "high"
    },
    {
      "topic": "EPDS Screening",
      "relevance": "high"
    },
    {
      "topic": "Baby Care Basics",
      "relevance": "medium"
    }
  ]
}
```

---

### Endpoint: Ingest PDF (Admin)

**Upload a PDF to add to the knowledge base.**

```http
POST /api/ingest
Content-Type: multipart/form-data
```

#### Request

```bash
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@document.pdf"
```

#### Response

```json
{
  "success": true,
  "message": "Successfully ingested 'document.pdf'",
  "chunks_created": 45
}
```

> **Note**: This endpoint should be protected with authentication in production.

---

## 6. Backend Integration Guide

### For Your Backend Team

#### Step 1: Add the Quiz Service URL

```python
# In your backend config
QUIZ_API_URL = "http://quiz-generator:8000"  # Docker internal
# or
QUIZ_API_URL = "http://localhost:8000"  # Local development
```

#### Step 2: Create a Quiz Service Client

```python
# quiz_service.py
import httpx
from typing import Optional, Dict, Any

class QuizService:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.timeout = 60.0  # Quiz generation can take time
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if quiz service is available."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/health",
                timeout=10.0
            )
            return response.json()
    
    async def generate_quiz(
        self, 
        topic: str, 
        num_questions: int = 5
    ) -> Dict[str, Any]:
        """
        Generate a quiz for a given topic.
        
        Args:
            topic: The subject matter for the quiz
            num_questions: Number of questions (1-20)
        
        Returns:
            Quiz data with questions, options, and explanations
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/quiz/generate",
                json={
                    "topic": topic,
                    "num_questions": num_questions
                },
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
    
    async def get_topics(self) -> Dict[str, Any]:
        """Get suggested quiz topics."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/topics",
                timeout=10.0
            )
            return response.json()


# Usage in your existing backend
quiz_service = QuizService()
```

#### Step 3: Integrate with Your Article Endpoints

```python
# In your article routes (example)
from fastapi import APIRouter, HTTPException
from quiz_service import quiz_service

router = APIRouter()

@router.post("/articles/{article_id}/generate-quiz")
async def generate_quiz_for_article(
    article_id: int,
    num_questions: int = 5
):
    """
    Generate a quiz based on an article's topic.
    Called when user clicks "Take Quiz" button.
    """
    # 1. Get the article from your database
    article = await get_article(article_id)
    if not article:
        raise HTTPException(404, "Article not found")
    
    # 2. Generate quiz using the quiz service
    try:
        quiz_data = await quiz_service.generate_quiz(
            topic=article.title,  # or article.topic
            num_questions=num_questions
        )
        
        if not quiz_data.get("success"):
            raise HTTPException(
                503, 
                quiz_data.get("message", "Quiz generation failed")
            )
        
        # 3. Optionally save quiz to your database
        # await save_quiz(article_id, quiz_data)
        
        return quiz_data
    
    except httpx.RequestError as e:
        raise HTTPException(503, f"Quiz service unavailable: {e}")
```

#### Step 4: Error Handling

```python
from fastapi import HTTPException
import httpx

async def safe_generate_quiz(topic: str, num_questions: int = 5):
    """Generate quiz with comprehensive error handling."""
    try:
        result = await quiz_service.generate_quiz(topic, num_questions)
        
        if not result.get("success"):
            # Quiz couldn't be generated (no relevant content)
            return {
                "success": False,
                "error": "no_content",
                "message": result.get("message", "No relevant content found")
            }
        
        return result
    
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "timeout",
            "message": "Quiz generation timed out. Please try again."
        }
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            return {
                "success": False,
                "error": "not_ready",
                "message": "Quiz system is initializing. Please try again."
            }
        raise
    
    except Exception as e:
        return {
            "success": False,
            "error": "unknown",
            "message": f"An error occurred: {str(e)}"
        }
```

---

## 7. Frontend Integration Examples

### JavaScript/TypeScript (Fetch)

```typescript
interface QuizQuestion {
  id: number;
  question: string;
  options: Array<{
    letter: string;
    text: string;
    is_correct: boolean;
  }>;
  correct_answer: string;
  explanation: string;
}

interface QuizResponse {
  success: boolean;
  topic: string;
  questions: QuizQuestion[];
  total_questions: number;
  message: string;
}

async function generateQuiz(
  topic: string, 
  numQuestions: number = 5
): Promise<QuizResponse> {
  const response = await fetch('/api/quiz/generate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      topic,
      num_questions: numQuestions,
    }),
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Usage
const quiz = await generateQuiz('postpartum depression', 5);
console.log(quiz.questions);
```

### React Hook Example

```tsx
import { useState } from 'react';

interface UseQuizReturn {
  quiz: QuizResponse | null;
  loading: boolean;
  error: string | null;
  generateQuiz: (topic: string, numQuestions?: number) => Promise<void>;
}

export function useQuiz(): UseQuizReturn {
  const [quiz, setQuiz] = useState<QuizResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateQuiz = async (topic: string, numQuestions = 5) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/quiz/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic, num_questions: numQuestions }),
      });

      const data = await response.json();
      
      if (!data.success) {
        setError(data.message || 'Failed to generate quiz');
        return;
      }
      
      setQuiz(data);
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return { quiz, loading, error, generateQuiz };
}

// Usage in component
function QuizButton({ articleTopic }: { articleTopic: string }) {
  const { quiz, loading, error, generateQuiz } = useQuiz();

  return (
    <div>
      <button 
        onClick={() => generateQuiz(articleTopic)}
        disabled={loading}
      >
        {loading ? 'Generating...' : 'Take Quiz'}
      </button>
      
      {error && <p className="error">{error}</p>}
      
      {quiz && (
        <QuizDisplay questions={quiz.questions} />
      )}
    </div>
  );
}
```

---

## 8. Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Required: Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Custom ChromaDB path
CHROMA_PERSIST_DIRECTORY=./chroma_db

# Optional: Custom collection name
CHROMA_COLLECTION_NAME=quiz_documents
```

### CORS Configuration

Edit `api.py` to add your frontend domains:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",           # React dev
        "https://your-production-domain.com",  # Production
        "https://early-motherhood-app.com",    # Your app
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 9. Deployment

### Docker Deployment (Recommended)

#### 1. Prepare Environment

```bash
# Create .env file
echo "GOOGLE_API_KEY=your_key_here" > .env

# Create PDFs directory
mkdir pdfs
cp your_documents/*.pdf pdfs/
```

#### 2. Build and Run

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# View logs
docker-compose logs -f quiz-api
```

#### 3. Ingest PDFs

```bash
# Copy PDFs to the container's pdfs directory (mounted volume)
# Then ingest via API:
curl -X POST "http://localhost:8000/api/ingest" \
  -F "file=@pdfs/maternal_health.pdf"
```

### Production Checklist

| Task | Status | Notes |
|------|--------|-------|
| Set production API key | [ ] | Create new key for production |
| Configure CORS origins | [ ] | Remove `*`, add exact domains |
| Add authentication to /api/ingest | [ ] | Protect admin endpoints |
| Set up HTTPS | [ ] | Use reverse proxy (nginx) |
| Configure rate limiting | [ ] | Prevent API abuse |
| Set up monitoring | [ ] | Track API usage and errors |
| Backup chroma_db | [ ] | Regular backups of vector DB |

### Docker Compose for Production

```yaml
version: '3.8'

services:
  quiz-api:
    build: .
    container_name: quiz-generator-api
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
    volumes:
      - ./chroma_db:/app/chroma_db
      - ./pdfs:/app/pdfs
    restart: always
    
  # Optional: Add nginx reverse proxy
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - quiz-api
```

---

## 10. Troubleshooting

### Common Issues

#### Issue: "Knowledge base not initialized"

**Cause**: No PDFs have been ingested yet.

**Solution**:
```bash
python main.py --ingest your_document.pdf
# or via API:
curl -X POST "http://localhost:8000/api/ingest" -F "file=@doc.pdf"
```

#### Issue: "Google API quota exceeded"

**Cause**: Too many API requests to Gemini.

**Solution**:
- Wait 1 minute (rate limit) or 24 hours (daily quota)
- Reduce `num_questions` per request
- Cache generated quizzes in your database

#### Issue: "No relevant content found for topic"

**Cause**: The topic doesn't match ingested PDF content.

**Solution**:
- Try a different topic wording
- Check `/api/topics` for suggested topics
- Ingest more relevant PDFs

#### Issue: First request is slow

**Cause**: HuggingFace model loading on first use.

**Solution**: This is normal. First request takes 10-30 seconds as the embedding model loads. Subsequent requests are fast.

### Getting Help

1. Check the Swagger docs: http://localhost:8000/docs
2. Review API logs: `docker-compose logs -f`
3. Test health endpoint: `curl http://localhost:8000/api/health`

---

## Quick Reference

### API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/quiz/generate` | Generate quiz |
| GET | `/api/topics` | Get topic suggestions |
| POST | `/api/ingest` | Upload PDF (admin) |
| GET | `/docs` | Swagger documentation |

### Generate Quiz - Quick Example

```bash
curl -X POST "http://localhost:8000/api/quiz/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "maternal health", "num_questions": 5}'
```

---

*Documentation Version: 1.0.0*  
*Last Updated: January 2026*

