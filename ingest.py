"""
Ingestion Module for Quiz Generator System
==========================================

This module handles the first phase of the RAG (Retrieval-Augmented Generation) pipeline:
1. Load PDF documents
2. Split text into manageable chunks
3. Convert chunks to vector embeddings using LOCAL HuggingFace model (FREE!)
4. Store vectors in ChromaDB for persistent retrieval

HYBRID ARCHITECTURE:
- Embeddings: Local HuggingFace model (all-MiniLM-L6-v2) - FREE, UNLIMITED
- LLM: Google Gemini - Only used for quiz generation (saves API quota)

RAG Flow - Ingestion Phase:
    PDF Document -> Text Extraction -> Chunking -> Local Embedding -> Vector Storage
"""

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader, BSHTMLLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # LOCAL - Free & Unlimited!
from langchain_chroma import Chroma
from langchain_core.documents import Document

# Load environment variables from .env file
load_dotenv()

# Constants for vector database configuration
CHROMA_PERSIST_DIRECTORY = "./chroma_db"
COLLECTION_NAME = "quiz_documents"

# Local embedding model - runs on CPU, no API calls needed
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Initialize LOCAL HuggingFace Embeddings.
    
    Uses 'all-MiniLM-L6-v2' - a small, fast, and high-quality model that runs
    entirely on your CPU. No API calls, no quotas, completely free!
    
    The model will be downloaded on first use (~80MB) and cached locally.
    
    Returns:
        HuggingFaceEmbeddings: Configured local embedding model instance.
    """
    print("   [*] Loading local embedding model (runs on CPU - FREE!)...")
    
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL_NAME,
        model_kwargs={'device': 'cpu'},  # Use CPU (works everywhere)
        encode_kwargs={'normalize_embeddings': True}  # Better similarity search
    )
    
    return embeddings


def _ingest_documents(documents: List[Document]) -> Chroma:
    """
    Common logic for chunking and storing documents in ChromaDB.
    """
    # Filter out empty pages
    documents = [doc for doc in documents if doc.page_content.strip()]
    
    if not documents:
        raise ValueError(
            "No extractable text found in the provided documents."
        )
    
    total_chars = sum(len(doc.page_content) for doc in documents)
    print(f"   [OK] Extracted {total_chars} characters of text")
    
    # Step 2: Split documents into chunks
    min_chunk_size = 100
    default_chunk_size = 1000
    default_overlap = 200
    
    if total_chars < default_chunk_size:
        chunk_size = max(min_chunk_size, total_chars // 2)
        chunk_overlap = min(50, chunk_size // 4)
        print(f"   [INFO] Small document, using chunk_size={chunk_size}, overlap={chunk_overlap}")
    else:
        chunk_size = default_chunk_size
        chunk_overlap = default_overlap
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"   [OK] Split into {len(chunks)} chunks")
    
    # Handle edge case where chunking produces no results
    if not chunks:
        chunks = [
            Document(page_content=doc.page_content, metadata=doc.metadata)
            for doc in documents
            if doc.page_content.strip()
        ]
        print("   [!] Using full pages as chunks")
    
    # Filter out whitespace-only chunks
    chunks = [chunk for chunk in chunks if chunk.page_content.strip()]
    
    if not chunks:
        raise ValueError("No content available to embed after processing.")
    
    # Step 3 & 4: Create LOCAL embeddings and store in ChromaDB
    print(f"   [...] Generating embeddings locally...")
    
    embeddings = get_embeddings()
    
    # Create or load vector store
    if vectorstore_exists():
        vectorstore = Chroma(
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            embedding_function=embeddings,
            collection_name=COLLECTION_NAME
        )
        vectorstore.add_documents(chunks)
    else:
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=CHROMA_PERSIST_DIRECTORY,
            collection_name=COLLECTION_NAME
        )
    
    print(f"   [OK] Stored {len(chunks)} chunks in ChromaDB at '{CHROMA_PERSIST_DIRECTORY}'")
    return vectorstore


def ingest_pdf(pdf_path: str) -> Chroma:
    """
    Ingest a PDF document into the ChromaDB vector store.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    print(f"[*] Loading PDF: {pdf_path}")
    loader = PyPDFLoader(str(pdf_path))
    documents = loader.load()
    print(f"   [OK] Loaded {len(documents)} pages from PDF")
    
    return _ingest_documents(documents)


def ingest_html(html_path: str) -> Chroma:
    """
    Ingest an HTML document into the ChromaDB vector store.
    """
    html_path = Path(html_path)
    if not html_path.exists():
        raise FileNotFoundError(f"HTML file not found: {html_path}")
    
    print(f"[*] Loading HTML: {html_path}")
    loader = BSHTMLLoader(str(html_path))
    documents = loader.load()
    print(f"   [OK] Loaded HTML content")
    
    return _ingest_documents(documents)


def ingest_text(text: str, metadata: dict = None) -> Chroma:
    """
    Ingest raw text into the ChromaDB vector store.
    """
    print("[*] Loading raw text content")
    documents = [Document(page_content=text, metadata=metadata or {})]
    return _ingest_documents(documents)


def load_vectorstore() -> Chroma:
    """
    Load an existing ChromaDB vector store from disk.
    
    Uses the SAME local embedding model that was used during ingestion.
    This is critical - you must use the same embedding model for both
    ingestion and retrieval!
    
    Returns:
        Chroma: The loaded vector store instance.
    
    Raises:
        FileNotFoundError: If the ChromaDB directory doesn't exist.
    """
    if not Path(CHROMA_PERSIST_DIRECTORY).exists():
        raise FileNotFoundError(
            f"Vector database not found at '{CHROMA_PERSIST_DIRECTORY}'. "
            "Please run ingestion first using ingest_pdf()."
        )
    
    # Use the SAME local embedding model
    embeddings = get_embeddings()
    
    vectorstore = Chroma(
        persist_directory=CHROMA_PERSIST_DIRECTORY,
        embedding_function=embeddings,
        collection_name=COLLECTION_NAME
    )
    
    return vectorstore


def vectorstore_exists() -> bool:
    """
    Check if a ChromaDB vector store already exists.
    
    Returns:
        bool: True if the vector store exists, False otherwise.
    """
    chroma_path = Path(CHROMA_PERSIST_DIRECTORY)
    return chroma_path.exists() and any(chroma_path.iterdir())


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python ingest.py <path_to_pdf>")
        print("Example: python ingest.py ./sample.pdf")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    ingest_pdf(pdf_file)
