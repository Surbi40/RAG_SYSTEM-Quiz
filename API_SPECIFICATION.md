# Quiz Generator API Specification
**For Backend Team Integration**

---

## Base URL
```
http://localhost:8000
```

---

## Authentication
Currently none (add your auth middleware as needed)

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /api/health`

**Purpose:** Check if API and database are ready

**Response:**
```json
{
    "status": "healthy",
    "database_ready": true,
    "message": "Ready to generate quizzes"
}
```

---

### 2. Generate Quiz ⭐ (Main Endpoint)

**Endpoint:** `POST /api/quiz/generate`

**Content-Type:** `application/json`

**Request Body:**
```json
{
    "topic": "postpartum depression",
    "num_questions": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Quiz topic (2-200 chars) |
| `num_questions` | integer | No | Number of questions (1-20, default: 5) |

**Success Response (200):**
```json
{
    "success": true,
    "topic": "postpartum depression",
    "questions": [
        {
            "id": 1,
            "question": "What is the primary purpose of the EPDS screening tool?",
            "options": [
                {
                    "letter": "A",
                    "text": "To diagnose postpartum depression definitively",
                    "is_correct": false
                },
                {
                    "letter": "B",
                    "text": "To screen for risk of postpartum depression",
                    "is_correct": true
                },
                {
                    "letter": "C",
                    "text": "To prescribe medication",
                    "is_correct": false
                },
                {
                    "letter": "D",
                    "text": "To measure baby's health",
                    "is_correct": false
                }
            ],
            "correct_answer": "To screen for risk of postpartum depression",
            "explanation": "The Edinburgh Postnatal Depression Scale (EPDS) is a screening tool designed to identify mothers who may be at risk for postpartum depression. It is not a diagnostic tool but helps healthcare providers determine who needs further evaluation."
        }
    ],
    "total_questions": 5,
    "message": "Quiz generated successfully"
}
```

**Error Response (503 - Database not ready):**
```json
{
    "detail": "Knowledge base not initialized. Please ingest PDF documents first."
}
```

**No Content Response (200):**
```json
{
    "success": false,
    "topic": "unknown topic",
    "questions": [],
    "total_questions": 0,
    "message": "Could not generate quiz for this topic. Try a different topic."
}
```

---

### 3. Get Suggested Topics

**Endpoint:** `GET /api/topics`

**Purpose:** Get list of recommended quiz topics

**Response:**
```json
{
    "success": true,
    "topics": [
        {"topic": "Postpartum Depression", "relevance": "high"},
        {"topic": "EPDS Screening", "relevance": "high"},
        {"topic": "Baby Care Basics", "relevance": "medium"},
        {"topic": "Breastfeeding", "relevance": "medium"},
        {"topic": "Maternal Mental Health", "relevance": "high"}
    ]
}
```

---

### 4. Ingest PDF (Admin Only)

**Endpoint:** `POST /api/ingest`

**Content-Type:** `multipart/form-data`

**Request:**
```
file: <PDF file>
```

**Response:**
```json
{
    "success": true,
    "message": "Successfully ingested 'document.pdf'",
    "chunks_created": 33
}
```

---

## How to Run

### Option 1: Direct Python
```bash
cd D:\RAG_system
python api.py
```

### Option 2: Uvicorn
```bash
cd D:\RAG_system
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Option 3: Production (with workers)
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Environment Variables

Create `.env` file:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

---

## CORS

Currently allows all origins. Modify `api.py` line 103-112 to restrict:

```python
allow_origins=[
    "https://your-production-domain.com",
    "https://api.your-domain.com",
]
```

---

## Response Times

| Operation | Typical Time |
|-----------|--------------|
| Health Check | ~100ms |
| Quiz Generation | 5-15 seconds |
| PDF Ingestion | 10-60 seconds |

---

## Rate Limits

Depends on Google Gemini API quota:
- Free tier: ~60 requests/minute
- Paid tier: Higher limits

---

## Error Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 500 | Server error |
| 503 | Database not ready |

---

## Testing with cURL

```bash
# Health check
curl http://localhost:8000/api/health

# Generate quiz
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "postpartum depression", "num_questions": 3}'

# Get topics
curl http://localhost:8000/api/topics
```

---

## Swagger Documentation

Access interactive API docs at:
```
http://localhost:8000/docs
```

