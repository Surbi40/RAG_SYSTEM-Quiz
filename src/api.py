"""
Quiz Generator API - FastAPI REST Service
==========================================

This module provides a REST API for the Quiz Generator System,
designed for integration with the Early Motherhood Support System.

Endpoints:
    POST /api/quiz/generate  - Generate a quiz from a topic
    POST /api/ingest         - Ingest a new PDF document
    GET  /api/health         - Health check endpoint
    GET  /api/topics         - Get suggested topics from ingested content

Usage:
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
"""

import os
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from ingest import ingest_pdf, ingest_html, ingest_text, vectorstore_exists, load_vectorstore
from generator import generate_quiz_safe

# =============================================================================
# API Models (Request/Response Schemas)
# =============================================================================

class QuizRequest(BaseModel):
    """Request model for quiz generation."""
    topic: str = Field(
        ..., 
        description="The topic for the quiz (e.g., 'postpartum depression', 'baby care')",
        min_length=2,
        max_length=200
    )
    num_questions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of questions to generate (1-20)"
    )

class QuizOption(BaseModel):
    """A single quiz option."""
    letter: str
    text: str
    is_correct: bool

class QuizQuestionResponse(BaseModel):
    """Response model for a single quiz question."""
    id: int
    question: str
    options: List[QuizOption]
    correct_answer: str
    explanation: str

class QuizResponse(BaseModel):
    """Response model for generated quiz."""
    success: bool
    topic: str
    questions: List[QuizQuestionResponse]
    total_questions: int
    message: str = ""

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    database_ready: bool
    message: str

class IngestResponse(BaseModel):
    """Response for PDF ingestion."""
    success: bool
    message: str
    chunks_created: int = 0

class TopicSuggestion(BaseModel):
    """A suggested topic based on ingested content."""
    topic: str
    relevance: str

class AnonymousArticle(BaseModel):
    """Model for anonymous text contributions."""
    text: str = Field(..., min_length=10)
    title: Optional[str] = Field(default="Anonymous Contribution")

class TopicsResponse(BaseModel):
    """Response for topic suggestions."""
    success: bool
    topics: List[TopicSuggestion]


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="Quiz Generator API",
    description="""
    RAG-powered Quiz Generator for the Early Motherhood Support System.
    
    This API generates educational quizzes based on ingested PDF content
    about maternal health, postpartum care, and baby development.
    
    ## Features
    - Generate quizzes from any topic in your knowledge base
    - Adaptive learning with detailed explanations
    - JSON responses ready for frontend integration
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration - Allow your frontend domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server
        "http://localhost:5173",      # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://your-domain.com",    # Production domain
        "*"                           # Allow all (for development only!)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Quiz Generator API",
        "version": "1.0.0",
        "description": "RAG-powered Quiz Generator for Early Motherhood Support System",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Use this to verify the API is running and the database is ready.
    """
    db_ready = vectorstore_exists()
    
    return HealthResponse(
        status="healthy" if db_ready else "degraded",
        database_ready=db_ready,
        message="Ready to generate quizzes" if db_ready else "No knowledge base found. Please ingest PDFs first."
    )


@app.post("/api/quiz/generate", response_model=QuizResponse, tags=["Quiz"])
async def generate_quiz_endpoint(request: QuizRequest):
    """
    Generate a quiz based on a topic.
    
    This endpoint:
    1. Searches the knowledge base for relevant content
    2. Uses AI to generate quiz questions
    3. Returns structured JSON for frontend display
    
    **Example Request:**
    ```json
    {
        "topic": "postpartum depression symptoms",
        "num_questions": 5
    }
    ```
    
    **Integration Example (JavaScript):**
    ```javascript
    const response = await fetch('/api/quiz/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            topic: 'postpartum depression',
            num_questions: 5
        })
    });
    const quiz = await response.json();
    ```
    """
    # Check if database exists
    if not vectorstore_exists():
        raise HTTPException(
            status_code=503,
            detail="Knowledge base not initialized. Please ingest PDF documents first."
        )
    
    # Generate the quiz
    result = generate_quiz_safe(request.topic, request.num_questions)
    
    # Check if generation was successful
    if not result.get("context_available", True) or not result.get("questions"):
        return QuizResponse(
            success=False,
            topic=request.topic,
            questions=[],
            total_questions=0,
            message=result.get("message", "Could not generate quiz for this topic. Try a different topic.")
        )
    
    # Transform questions to response format
    formatted_questions = []
    for idx, q in enumerate(result.get("questions", []), 1):
        options = []
        for i, opt in enumerate(q.get("options", [])):
            letter = chr(65 + i)  # A, B, C, D
            options.append(QuizOption(
                letter=letter,
                text=opt,
                is_correct=(opt == q.get("correct_answer"))
            ))
        
        formatted_questions.append(QuizQuestionResponse(
            id=idx,
            question=q.get("question", ""),
            options=options,
            correct_answer=q.get("correct_answer", ""),
            explanation=q.get("explanation", "")
        ))
    
    return QuizResponse(
        success=True,
        topic=request.topic,
        questions=formatted_questions,
        total_questions=len(formatted_questions),
        message="Quiz generated successfully"
    )


@app.post("/api/ingest", response_model=IngestResponse, tags=["Admin"])
async def ingest_pdf_endpoint(file: UploadFile = File(...)):
    """
    Ingest a PDF document into the knowledge base.
    
    Upload PDF files containing maternal health content to expand
    the quiz knowledge base.
    
    **Note:** This is an admin endpoint. In production, protect this
    with authentication.
    """
    # Detect file type
    is_pdf = file.filename.lower().endswith('.pdf')
    is_html = file.filename.lower().endswith(('.html', '.htm'))

    if not (is_pdf or is_html):
        raise HTTPException(
            status_code=400,
            detail="Only PDF and HTML files are supported"
        )
    
    # Save uploaded file temporarily
    temp_path = Path(f"./temp_{file.filename}")
    try:
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest the file based on extension
        if is_pdf:
            vectorstore = ingest_pdf(str(temp_path))
        else:
            vectorstore = ingest_html(str(temp_path))
        
        # Get chunk count (approximate)
        collection = vectorstore._collection
        chunk_count = collection.count() if collection else 0
        
        return IngestResponse(
            success=True,
            message=f"Successfully ingested '{file.filename}'",
            chunks_created=chunk_count
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest file: {str(e)}"
        )
    
    finally:
        # Clean up temp file
        if temp_path.exists():
            temp_path.unlink()


@app.post("/api/articles/anonymous", response_model=IngestResponse, tags=["Articles"])
async def submit_anonymous_article(article: AnonymousArticle):
    """
    Submit an anonymous text article.
    
    The content will be processed and added to the knowledge base 
    for future quiz generation.
    """
    try:
        vectorstore = ingest_text(
            article.text, 
            metadata={"source": "anonymous", "title": article.title}
        )
        
        collection = vectorstore._collection
        chunk_count = collection.count() if collection else 0
        
        return IngestResponse(
            success=True,
            message=f"Successfully added anonymous article: {article.title}",
            chunks_created=chunk_count
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit article: {str(e)}"
        )


@app.get("/api/topics", response_model=TopicsResponse, tags=["Quiz"])
async def get_suggested_topics():
    """
    Get suggested quiz topics based on ingested content.
    
    Returns a list of topics that are likely to produce good quizzes
    based on the current knowledge base.
    """
    if not vectorstore_exists():
        return TopicsResponse(
            success=False,
            topics=[]
        )
    
    # Predefined topics relevant to Early Motherhood Support
    # In production, you could dynamically extract these from the content
    suggested_topics = [
        TopicSuggestion(topic="Postpartum Depression", relevance="high"),
        TopicSuggestion(topic="EPDS Screening", relevance="high"),
        TopicSuggestion(topic="Baby Care Basics", relevance="medium"),
        TopicSuggestion(topic="Breastfeeding", relevance="medium"),
        TopicSuggestion(topic="Maternal Mental Health", relevance="high"),
        TopicSuggestion(topic="Sleep Tips for New Mothers", relevance="medium"),
        TopicSuggestion(topic="Newborn Development", relevance="medium"),
    ]
    
    return TopicsResponse(
        success=True,
        topics=suggested_topics
    )


# =============================================================================
# Run Server
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Starting Quiz Generator API Server")
    print("="*60)
    print("API Docs: http://localhost:8000/docs")
    print("Health:   http://localhost:8000/api/health")
    print("="*60 + "\n")
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

