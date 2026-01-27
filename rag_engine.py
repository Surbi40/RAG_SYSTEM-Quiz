import os
import json

# --- 1. Loaders (Community) ---
from langchain_community.document_loaders import PyPDFLoader

# --- 2. Text Splitter (NEW PACKAGE) ---
# OLD: from langchain.text_splitter import ...
# NEW:
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- 3. Embeddings & Vector Store ---
from langchain_huggingface import HuggingFaceEmbeddings
import os
import json
from glob import glob

# --- 1. Loaders (Community) ---
from langchain_community.document_loaders import PyPDFLoader

# --- 2. Text Splitter ---
from langchain_text_splitters import RecursiveCharacterTextSplitter

# --- 3. Embeddings & Vector Store ---
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# --- 4. LLM ---
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 5. Prompts ---
from langchain_core.prompts import PromptTemplate

# --- 6. Chains ---
from langchain.chains import create_retrieval_chain

# -------------------------
# 1. API KEY (Google Gemini)
# -------------------------
os.environ["GOOGLE_API_KEY"] = "AIzaSyCl6QRVcn1ZSLI5W_HrPZOc9R7qCDsqPag"

# -------------------------
# 2. Embeddings
# -------------------------
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# -------------------------
# 3. Vector DB Directory
# -------------------------
DB_DIR = "./chroma_db_store"

# -------------------------
# 4. PDF Ingestion Function (Multi-PDF friendly)
# -------------------------
def ingest_pdf_to_vector_db(pdf_paths):
    """
    Reads PDFs, chunks them, and adds to Chroma Vector DB.
    Can handle single PDF path or list of paths.
    """
    if isinstance(pdf_paths, str):
        pdf_paths = [pdf_paths]

    # Load existing DB if exists
    vector_db = None
    if os.path.exists(DB_DIR):
        vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_function)
    else:
        vector_db = Chroma(embedding_function=embedding_function, persist_directory=DB_DIR)

    for file_path in pdf_paths:
        loader = PyPDFLoader(file_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        chunks = splitter.split_documents(docs)

        # Add new chunks to existing DB
        vector_db.add_documents(chunks)
        print(f"[INFO] Ingested: {file_path}")

    # Save updated DB
    vector_db.persist()
    print("[INFO] Vector DB updated with all PDFs.")
    return True

# -------------------------
# 5. Quiz Generation Function
# -------------------------
def generate_quiz_rag(topic_query, difficulty="Medium"):
    """
    Queries Vector DB for context and generates a quiz using Gemini
    """
    # Load DB
    vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_function)
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    # Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)

    # Prompt template
    prompt_template = """
You are a quiz generator. Use the following CONTEXT from the user's article to create a quiz.

CONTEXT:
{context}

INSTRUCTION:
Create 3 {difficulty} multiple-choice questions based ONLY on the context above.
Return the output as a RAW JSON list. 
Format: [{{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..." }}]

Strictly JSON. No markdown.
"""
    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "difficulty"]
    )

    # Create retrieval chain
    qa_chain = create_retrieval_chain(
        retriever=retriever,
        llm=llm,
        combine_documents_chain_kwargs={"prompt": PROMPT},
        return_source_documents=True
    )

    # Execute query
    response = qa_chain.invoke({"input": topic_query, "difficulty": difficulty})

    # Parse JSON safely
    try:
        raw_text = response["output_text"]
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]
        return json.loads(raw_text)
    except Exception as e:
        print(f"[ERROR] Parsing JSON failed: {e}")
        return []

# -------------------------
# 6. Example Usage
# -------------------------
if __name__ == "__main__":
    # Ingest all PDFs in folder
    pdf_files = glob("pdfs/*.pdf")  # Put your PDFs in a 'pdfs' folder
    ingest_pdf_to_vector_db(pdf_files)

    # Generate quiz
    quiz = generate_quiz_rag("Explain the main concepts in these articles.", difficulty="Easy")
    print(json.dumps(quiz, indent=2))

from langchain_chroma import Chroma

# --- 4. LLM (Google) ---
from langchain_google_genai import ChatGoogleGenerativeAI

# --- 5. Prompts (Core) ---
# OLD: from langchain.prompts import PromptTemplate
# NEW:
from langchain_core.prompts import PromptTemplate

# --- 6. Chains ---
from langchain.chains import create_retrieval_chain

# 1. SETUP API KEY
os.environ["GOOGLE_API_KEY"] = "AIzaSyCl6QRVcn1ZSLI5W_HrPZOc9R7qCDsqPag"

# 2. SETUP EMBEDDINGS (The "Translator" to Vectors)
# We use HuggingFace (runs locally/free) to create vectors, 
# and Gemini to generate text. This saves money and is faster.
embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 3. DIRECTORY TO SAVE VECTORS
DB_DIR = "./chroma_db_store"

def ingest_pdf_to_vector_db(file_path):
    """Reads PDF, chunks it, and saves to Vector DB"""
    # A. Load PDF
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    
    # B. Split Text (Critical for RAG)
    # We split into 1000 character chunks with 200 overlap to keep context
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    
    # C. Store in ChromaDB
    # This creates a folder on your disk
    vector_db = Chroma.from_documents(
        documents=chunks, 
        embedding=embedding_function,
        persist_directory=DB_DIR
    )
    return True

def generate_quiz_rag(topic_query, difficulty="Medium"):
    """Queries Vector DB for context, then sends to Gemini"""
    
    # A. Load the existing DB
    vector_db = Chroma(persist_directory=DB_DIR, embedding_function=embedding_function)
    
    # B. Create Retriever
    # Fetch the top 3 most relevant chunks regarding the topic
    retriever = vector_db.as_retriever(search_kwargs={"k": 3})
    
    # C. Setup Gemini
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    
    # D. The Prompt (Instruction to Gemini)
    prompt_template = """
    You are a quiz generator. Use the following CONTEXT from the user's article to create a quiz.
    
    CONTEXT:
    {context}
    
    INSTRUCTION:
    Create 3 {difficulty} multiple-choice questions based ONLY on the context above.
    Return the output as a RAW JSON list. 
    Format: [{{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..." }}]
    
    Strictly JSON. No markdown.
    """
    
    PROMPT = PromptTemplate(
        template=prompt_template, 
        input_variables=["context", "difficulty"]
    )
    
    # E. The Chain (Link DB -> Prompt -> Gemini)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    # F. Execute
    response = qa_chain.invoke({"query": topic_query})
    
    # G. Parse JSON
    try:
        raw_text = response['result']
        # Clean up Gemini's markdown if present
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0]
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0]
            
        return json.loads(raw_text)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return []