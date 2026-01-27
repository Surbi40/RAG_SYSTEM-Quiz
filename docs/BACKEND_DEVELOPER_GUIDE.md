# Backend Developer Guide: Quiz Generation (RAG) System

This guide is designed for the backend developer integrating the Quiz Generator into the **Early Motherhood Support System**.

---

## 🚀 1. Setup & Installation

### Prerequisites
- **Python**: 3.10+
- **Google AI API Key**: Get one from [Google AI Studio](https://aistudio.google.com/).

### Quick Commands (Copy & Paste)
```bash
# 1. Clone your repo
git clone https://github.com/Surbi40/RAG_SYSTEM-Quiz.git
cd RAG_SYSTEM-Quiz

# 2. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate      # Windows
source venv/bin/activate    # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
echo GOOGLE_API_KEY=your_key_here > .env
```

---

## 🏃 2. Running the System

| Task | Command |
| :--- | :--- |
| **Start API Server** | `python src/api.py` |
| **Ingest PDF** | `python src/main.py --ingest document.pdf` |
| **Interactive Mode** | `python src/main.py` |
| **Run Health Tests** | `python src/test_api.py` |
| **Start with Docker** | `docker-compose up --build -d` |

---

## 🧠 3. Management of Knowledge (ChromaDB)

The system uses **ChromaDB** for vector storage. This folder (`chroma_db/`) is git-ignored. You have two ways to build the database:

### Option A: The CLI Method (Initial Seeding)
Put your source PDFs in a folder and run:
```bash
python main.py --ingest ./path/to/document.pdf
```

### Option B: The API Method (Dynamic Growth)
Use the API to upload documents programmatically:
- **Endpoint**: `POST /api/ingest`
- **Method**: Multipart Form Data (`file=@yourdoc.pdf`)

---

## 🔗 3. Integration Scenarios

### Scenario 1: New Community Post -> Add to "Brain"
When a user submits an anonymous article or a clinical post, you should automatically index it so other users can take a quiz on it.
- **Endpoint**: `POST /api/articles/anonymous`
- **Payload**:
  ```json
  {
    "title": "Clinical Tip of the Day",
    "text": "The full content of the post goes here..."
  }
  ```

### Scenario 2: User requests a Quiz
When a user clicks "Take Quiz" on a specific topic:
- **Endpoint**: `POST /api/quiz/generate`
- **Payload**:
  ```json
  {
    "topic": "postpartum depression symptoms",
    "num_questions": 5
  }
  ```
- **Handling the Response**: The response is a structured JSON array. You should pass this directly to your frontend.

---

## 🐳 4. Deployment (Docker)

The system is ready for production using Docker.
```bash
docker-compose up --build -d
```
**Volumes**: The `docker-compose.yml` is configured to map the `chroma_db` folder to a volume. This ensures your knowledge base isn't lost when the container is deleted.

---

## 🛠 5. Core Files & Responsibility
- `api.py`: API endpoints and CORS configuration.
- `ingest.py`: Handles the RAG Ingestion pipeline (Loader -> Splitter -> Local Embedding -> Chroma).
- `generator.py`: Handles the RAG Generation pipeline (Query -> Retriever -> Gemini Pro -> Pydantic Validation).
- `requirements.txt`: Project dependencies (LangChain, FastAPI, Google-GenerativeAI).

---

## 📢 6. API Documentation
Once the server is running, you can access the full interactive spec at:
**`http://localhost:8000/docs`**
