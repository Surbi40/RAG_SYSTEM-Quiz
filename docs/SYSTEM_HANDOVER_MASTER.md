# Quiz Generation System: Master Handover Guide

This document summarizes the overall architecture, features, and integration steps for the Quiz Generation System (RAG-powered).

---

## 1. System Overview & Architecture
The system uses **Retrieval-Augmented Generation (RAG)** to create educational quizzes from specific documents.

### How it Works:
- **Phase 1: Ingestion (Learning)**
  - It reads PDFs, HTML, or raw text.
  - It uses a **Local AI Model** (HuggingFace `all-MiniLM-L6-v2`) to convert text into vectors.
  - These vectors are stored in **ChromaDB** (a local vector database).
- **Phase 2: Generation (Recalling)**
  - When a user asks for a quiz, the system finds the most relevant text chunks.
  - It sends these chunks as "Context" to **Google Gemini**.
  - Gemini generates a high-quality JSON quiz with questions, options, and explanations.

---

## 2. Key Features
- **PDF/HTML Support**: Batch ingestion of health documents.
- **Anonymous Post Integration**: 
  - The system accepts raw text from user posts.
  - **Flow**: User Post -> Backend API -> `POST /api/articles/anonymous` -> Instant indexing.
  - Once indexed, a quiz can be generated about that specific user post.
- **Adaptive Learning**: Every question comes with a detailed educational explanation.

---

## 3. Backend Developer Handover
### ✅ Checklist:
1.  **Secrets**: Provide the `GOOGLE_API_KEY`. It must be placed in a `.env` file.
2.  **Database**: Include the `chroma_db/` folder in the handover. It contains all existing "learned" content.
3.  **API Integration**:
    - Call `POST /api/ingest` for file uploads.
    - Call `POST /api/articles/anonymous` whenever a community post is created.
4.  **Deployment**: The system is fully **Dockerized**. They can use `docker-compose up --build -d` for production-ready deployment.

---

## 4. Frontend Developer Handover
### ✅ Checklist:
1.  **Docs**: Direct them to `http://localhost:8000/docs` for the interactive Swagger UI.
2.  **Data Structure**: Quizzes are JSON arrays. Each object has:
    - `question` (String)
    - `options` (Array of objects with `letter`, `text`, `is_correct`)
    - `explanation` (String - to be shown after the user answers).
3.  **CORS**: Confirm the frontend domain to whitelist it in `api.py`.
4.  **User Experience**:
    - **Loading States**: AI generation takes 10–15 seconds. Use a spinner.
    - **Suggested Topics**: Use `GET /api/topics` to show available quiz categories.

---

## 5. Docker & Environment
The system is ready for one-command setup.
- **Dockerfile**: Builds the Python environment and installs dependencies.
- **Docker Compose**: Handles networking, environment variables, and **Persistence** (mapping `chroma_db` to the disk so data isn't lost).

---

## 6. API Quick Links (Local)
- **Interactive UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)
- **Suggested Topics**: [http://localhost:8000/api/topics](http://localhost:8000/api/topics)
