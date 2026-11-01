
import os
import json
from glob import glob

from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

from langchain_google_genai import ChatGoogleGenerativeAI

from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain


# --------------------------------------------------
# 1. ENVIRONMENT CONFIGURATION
# --------------------------------------------------

# Load variables from the project's .env file.
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is missing. Please configure it in your .env file."
    )


# --------------------------------------------------
# 2. CONFIGURATION
# --------------------------------------------------

DB_DIR = "./chroma_db_store"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

GEMINI_MODEL = "gemini-1.5-flash"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
RETRIEVER_K = 3


# --------------------------------------------------
# 3. INITIALIZE EMBEDDINGS
# --------------------------------------------------

embedding_function = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)


# --------------------------------------------------
# 4. PDF INGESTION
# --------------------------------------------------

def ingest_pdf_to_vector_db(pdf_paths):
    """
    Load one or multiple PDF files, split their content
    into chunks, and store the chunks in ChromaDB.

    Args:
        pdf_paths: A PDF path or a list of PDF paths.

    Returns:
        Number of documents ingested.
    """

    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]

    if not pdf_paths:
        raise ValueError("No PDF files were provided.")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

    vector_db = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding_function
    )

    total_chunks = 0

    for file_path in pdf_paths:

        if not os.path.isfile(file_path):
            print(f"[WARNING] File not found: {file_path}")
            continue

        if not file_path.lower().endswith(".pdf"):
            print(f"[WARNING] Skipping non-PDF file: {file_path}")
            continue

        print(f"[INFO] Processing: {file_path}")

        loader = PyPDFLoader(file_path)
        documents = loader.load()

        if not documents:
            print(f"[WARNING] No content found in: {file_path}")
            continue

        chunks = splitter.split_documents(documents)

        if not chunks:
            print(f"[WARNING] No text chunks created: {file_path}")
            continue

        vector_db.add_documents(chunks)

        total_chunks += len(chunks)

        print(
            f"[INFO] Ingested {len(chunks)} chunks from {file_path}"
        )

    print(
        f"[INFO] Ingestion completed. Total chunks: {total_chunks}"
    )

    return total_chunks


# --------------------------------------------------
# 5. QUIZ GENERATION USING RAG
# --------------------------------------------------

def generate_quiz_rag(topic_query, difficulty="Medium"):
    """
    Retrieve relevant document chunks from ChromaDB
    and use Gemini to generate multiple-choice questions.

    Args:
        topic_query: User's topic or question.
        difficulty: Easy, Medium, or Hard.

    Returns:
        A list of generated quiz questions.
    """

    if not topic_query or not topic_query.strip():
        raise ValueError("Topic query cannot be empty.")

    if not os.path.exists(DB_DIR):
        raise RuntimeError(
            "Vector database not found. Ingest PDFs first."
        )

    # A. Load existing vector database
    vector_db = Chroma(
        persist_directory=DB_DIR,
        embedding_function=embedding_function
    )

    # B. Create retriever
    retriever = vector_db.as_retriever(
        search_kwargs={"k": RETRIEVER_K}
    )

    # C. Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        temperature=0.3,
        google_api_key=GOOGLE_API_KEY
    )

    # D. Define the prompt
    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            """
You are an educational quiz generator.

Use ONLY the information provided in the retrieved context.

Retrieved context:
{context}

Generate exactly 3 {difficulty} multiple-choice questions.

Each question must have:
- One question.
- Four answer options.
- One correct answer.
- A short explanation based only on the context.

Return ONLY a valid JSON array.

Use this exact structure:

[
    {{
        "question": "Question text",
        "options": ["Option A", "Option B", "Option C", "Option D"],
        "answer": "Option A",
        "explanation": "Explanation based on the context"
    }}
]

Do not include Markdown code fences or additional text.
If the context does not contain enough information, do not invent facts.
            """
        ),
        (
            "human",
            "Generate a quiz about: {input}"
        )
    ])

    # E. Create document-combination chain
    document_chain = create_stuff_documents_chain(
        llm=llm,
        prompt=prompt
    )

    # F. Create retrieval chain
    rag_chain = create_retrieval_chain(
        retriever=retriever,
        combine_docs_chain=document_chain
    )

    # G. Execute RAG pipeline
    response = rag_chain.invoke({
        "input": topic_query,
        "difficulty": difficulty
    })

    # H. Extract generated answer
    raw_text = response.get("answer", "").strip()

    if not raw_text:
        print("[ERROR] Gemini returned an empty response.")
        return []

    # I. Remove Markdown code fences if Gemini includes them
    if raw_text.startswith("```"):
        raw_text = raw_text.replace("```json", "", 1)
        raw_text = raw_text.replace("```", "").strip()

    # J. Parse JSON
    try:
        quiz = json.loads(raw_text)

        if not isinstance(quiz, list):
            raise ValueError("Expected a JSON list.")

        return quiz

    except (json.JSONDecodeError, ValueError) as error:
        print(f"[ERROR] Failed to parse Gemini JSON: {error}")
        print("[DEBUG] Gemini response:", raw_text)
        return []


# --------------------------------------------------
# 6. EXAMPLE EXECUTION
# --------------------------------------------------

if __name__ == "__main__":

    pdf_files = glob("pdfs/*.pdf")

    if not pdf_files:
        print("[WARNING] No PDF files found in the pdfs directory.")
    else:

        # Ingest PDFs into ChromaDB
        ingest_pdf_to_vector_db(pdf_files)

        # Generate quiz
        quiz = generate_quiz_rag(
            "Explain the main concepts in these articles.",
            difficulty="Easy"
        )

        print("\nGenerated Quiz:")
        print(json.dumps(quiz, indent=4, ensure_ascii=False))
