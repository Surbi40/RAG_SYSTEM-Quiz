# Quiz Generator System 📚

A RAG (Retrieval-Augmented Generation) powered Quiz Generator for the **Early Motherhood Support System**.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     HYBRID ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   PDF       │ -> │   Local     │ -> │  ChromaDB   │         │
│  │   Files     │    │  Embedding  │    │  Storage    │         │
│  └─────────────┘    │ (FREE!)     │    └─────────────┘         │
│                     └─────────────┘                              │
│                           │                                      │
│                           ▼                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │   User      │ -> │  Semantic   │ -> │   Gemini    │         │
│  │   Topic     │    │  Search     │    │   LLM       │         │
│  └─────────────┘    │ (FREE!)     │    │  (1 call)   │         │
│                     └─────────────┘    └─────────────┘         │
│                                              │                   │
│                                              ▼                   │
│                                        ┌─────────────┐          │
│                                        │   Quiz      │          │
│                                        │   JSON      │          │
│                                        └─────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Features

- 🆓 **Local Embeddings** - HuggingFace model runs on CPU (FREE, unlimited)
- 🤖 **AI-Powered Quizzes** - Google Gemini generates intelligent questions
- 📄 **PDF Ingestion** - Upload any PDF to expand knowledge base
- 🌐 **REST API** - Easy integration with any frontend
- 📱 **CORS Enabled** - Works with React, Vue, Angular, etc.

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file:

```env
GOOGLE_API_KEY=your_api_key_here
```

### 3. Ingest PDF Documents

```bash
python main.py --ingest your_document.pdf
```

### 4. Start the API Server

```bash
python api.py
```

The API will be available at: http://localhost:8000

### 5. Test Quiz Generation

```bash
# Using CLI
python main.py --topic "postpartum depression" --num 5

# Using API
curl -X POST http://localhost:8000/api/quiz/generate \
  -H "Content-Type: application/json" \
  -d '{"topic": "postpartum depression", "num_questions": 5}'
```

## 📡 API Endpoints

### Health Check
```
GET /api/health
```

### Generate Quiz
```
POST /api/quiz/generate
Content-Type: application/json

{
    "topic": "postpartum depression",
    "num_questions": 5
}
```

Response:
```json
{
    "success": true,
    "topic": "postpartum depression",
    "questions": [
        {
            "id": 1,
            "question": "What is the EPDS used for?",
            "options": [
                {"letter": "A", "text": "...", "is_correct": false},
                {"letter": "B", "text": "...", "is_correct": true},
                {"letter": "C", "text": "...", "is_correct": false},
                {"letter": "D", "text": "...", "is_correct": false}
            ],
            "correct_answer": "B. ...",
            "explanation": "Detailed explanation..."
        }
    ],
    "total_questions": 5,
    "message": "Quiz generated successfully"
}
```

### Ingest PDF (Admin)
```
POST /api/ingest
Content-Type: multipart/form-data

file: <PDF file>
```

### Get Suggested Topics
```
GET /api/topics
```

## 🌐 Frontend Integration

### JavaScript Example

```javascript
async function generateQuiz(topic) {
    const response = await fetch('http://localhost:8000/api/quiz/generate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            topic: topic,
            num_questions: 5
        })
    });
    
    const quiz = await response.json();
    
    if (quiz.success) {
        displayQuiz(quiz.questions);
    } else {
        showError(quiz.message);
    }
}
```

### React Component Example

```jsx
import { useState } from 'react';

function QuizButton({ articleTopic }) {
    const [quiz, setQuiz] = useState(null);
    const [loading, setLoading] = useState(false);
    
    const handleClick = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/quiz/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: articleTopic,
                    num_questions: 5
                })
            });
            const data = await res.json();
            setQuiz(data);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <button onClick={handleClick} disabled={loading}>
            {loading ? 'Generating...' : 'Take Quiz'}
        </button>
    );
}
```

## 📁 Project Structure

```
D:\RAG_system\
├── api.py                    # FastAPI REST server
├── main.py                   # CLI interface
├── ingest.py                 # PDF ingestion module
├── generator.py              # Quiz generation module
├── requirements.txt          # Python dependencies
├── .env                      # API keys (create this)
├── docs/                     # Detailed technical documentation
│   ├── API_SPECIFICATION.md  # Detailed endpoint specs
│   ├── DOCUMENTATION.md      # Full architecture guide
│   ├── BACKEND_DEVELOPER_GUIDE.md # Handover instructions
│   └── SYSTEM_HANDOVER_MASTER.md  # Master system overview
├── chroma_db/                # Vector database (auto-created)
└── frontend_integration.html # Frontend example
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | Yes |

### Model Configuration

Edit `generator.py` to change the LLM model:

```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # or "gemini-2.5-pro"
    temperature=0.3,
)
```

Edit `ingest.py` to change the embedding model:

```python
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # or any sentence-transformers model
```

## 🚢 Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Remove `"*"` from CORS origins in `api.py`
- [ ] Add authentication to `/api/ingest` endpoint
- [ ] Set up proper logging
- [ ] Use environment-based configuration
- [ ] Add rate limiting
- [ ] Set up HTTPS

## 🔒 Security Notes

1. **API Key**: Never expose `GOOGLE_API_KEY` in frontend code
2. **Ingestion**: Protect the `/api/ingest` endpoint with admin auth
3. **CORS**: Restrict to your actual domain in production

## 📄 License

MIT License - Free for commercial use

---

Built with ❤️ for the Early Motherhood Support System
