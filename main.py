"""
Quiz Generator System - Main Entry Point
=========================================

This is the main script that orchestrates the complete RAG pipeline
for generating educational quizzes from PDF documents.

Complete RAG Pipeline Overview:
    +-------------------------------------------------------------------------+
    |                        INGESTION PHASE (One-time)                        |
    |  PDF -> Load -> Split into Chunks -> Embed with Gemini -> Store in ChromaDB |
    +-------------------------------------------------------------------------+
                                        |
                                        v
    +-------------------------------------------------------------------------+
    |                        GENERATION PHASE (Per Query)                      |
    |  Topic -> Similarity Search -> Retrieve Context -> Gemini LLM -> JSON Quiz  |
    +-------------------------------------------------------------------------+

Usage:
    python main.py                    # Interactive mode
    python main.py --ingest <pdf>     # Ingest a PDF file
    python main.py --topic <topic>    # Generate quiz for a topic
"""

import argparse
import json
import sys
from pathlib import Path

from ingest import ingest_pdf, vectorstore_exists
from generator import generate_quiz_safe


def print_banner():
    """Display the application banner."""
    banner = """
+====================================================================+
|                    QUIZ GENERATOR SYSTEM                           |
|              RAG-Powered Educational Quiz Generation               |
+--------------------------------------------------------------------+
|  Technology Stack:                                                 |
|  - LangChain for orchestration                                     |
|  - ChromaDB for vector storage                                     |
|  - Google Gemini for LLM & Embeddings                              |
+====================================================================+
"""
    print(banner)


def print_quiz(quiz: dict):
    """
    Pretty print the generated quiz in a readable format.
    
    Args:
        quiz: The quiz dictionary from the generator.
    """
    print("\n" + "="*70)
    print(f"[QUIZ] {quiz.get('topic', 'Unknown Topic').upper()}")
    print("="*70)
    
    if not quiz.get("context_available", True):
        print(f"\n[WARNING] {quiz.get('message', 'No context available.')}")
        return
    
    questions = quiz.get("questions", [])
    if not questions:
        print("\n[WARNING] No questions were generated.")
        return
    
    for i, q in enumerate(questions, 1):
        print(f"\n{'-'*70}")
        print(f"Question {i}: {q.get('question', 'N/A')}")
        print()
        
        options = q.get("options", [])
        for j, opt in enumerate(options):
            letter = chr(65 + j)  # A, B, C, D
            marker = "*" if opt == q.get("correct_answer") else " "
            print(f"   [{marker}] {letter}. {opt}")
        
        print(f"\n   Explanation: {q.get('explanation', 'N/A')}")
    
    print("\n" + "="*70)
    print(f"Total Questions: {len(questions)}")
    print("="*70)


def print_json_quiz(quiz: dict):
    """
    Print the quiz as formatted JSON.
    
    Args:
        quiz: The quiz dictionary from the generator.
    """
    print("\n" + "="*70)
    print("RAW JSON OUTPUT:")
    print("="*70)
    print(json.dumps(quiz, indent=2, ensure_ascii=False))
    print("="*70)


def get_sample_pdf_path() -> Path:
    """
    Look for a sample PDF in common locations.
    
    Returns:
        Path to sample PDF if found, None otherwise.
    """
    # Common locations to check for sample PDFs
    common_paths = [
        Path("./sample.pdf"),
        Path("./samples/sample.pdf"),
        Path("./data/sample.pdf"),
        Path("./documents/sample.pdf"),
    ]
    
    for path in common_paths:
        if path.exists():
            return path
    
    # Check for any PDF in current directory
    pdf_files = list(Path(".").glob("*.pdf"))
    if pdf_files:
        return pdf_files[0]
    
    return None


def interactive_mode():
    """
    Run the quiz generator in interactive mode.
    
    This mode guides the user through:
    1. Checking if a vector database exists
    2. Ingesting a PDF if needed
    3. Generating a quiz based on user input
    """
    print_banner()
    
    # Step 1: Check if vector database exists
    print("\n[*] Checking for existing vector database...")
    
    if vectorstore_exists():
        print("   [OK] Vector database found at './chroma_db'")
        print("   [INFO] Ready to generate quizzes from ingested documents.")
    else:
        print("   [!] No vector database found.")
        print("\n[*] You need to ingest a PDF first.")
        
        # Try to find a sample PDF
        sample_pdf = get_sample_pdf_path()
        
        if sample_pdf:
            print(f"   Found PDF: {sample_pdf}")
            response = input(f"   Ingest '{sample_pdf}'? (y/n): ").strip().lower()
            
            if response == 'y':
                try:
                    ingest_pdf(str(sample_pdf))
                except Exception as e:
                    print(f"\n[ERROR] Error during ingestion: {e}")
                    sys.exit(1)
            else:
                print("\n   Please provide a PDF path to ingest:")
                pdf_path = input("   PDF path: ").strip()
                if pdf_path:
                    try:
                        ingest_pdf(pdf_path)
                    except Exception as e:
                        print(f"\n[ERROR] Error during ingestion: {e}")
                        sys.exit(1)
                else:
                    print("\n[ERROR] No PDF provided. Exiting.")
                    sys.exit(1)
        else:
            print("\n   No PDF files found in current directory.")
            pdf_path = input("   Enter the path to a PDF file: ").strip()
            
            if pdf_path:
                try:
                    ingest_pdf(pdf_path)
                except Exception as e:
                    print(f"\n[ERROR] Error during ingestion: {e}")
                    sys.exit(1)
            else:
                print("\n[ERROR] No PDF provided. Exiting.")
                sys.exit(1)
    
    # Step 2: Get topic from user
    print("\n" + "-"*70)
    print("[*] QUIZ GENERATION")
    print("-"*70)
    
    topic = input("\n[>] Enter a topic for the quiz: ").strip()
    
    if not topic:
        print("[ERROR] No topic provided. Exiting.")
        sys.exit(1)
    
    # Get number of questions
    num_questions_str = input("[>] Number of questions (default: 5): ").strip()
    num_questions = int(num_questions_str) if num_questions_str.isdigit() else 5
    num_questions = max(1, min(num_questions, 20))  # Clamp between 1 and 20
    
    # Ask for output format
    output_format = input("[>] Output format - (p)retty or (j)son? (default: p): ").strip().lower()
    
    # Step 3: Generate the quiz
    print(f"\n[...] Generating {num_questions} questions about '{topic}'...")
    
    quiz = generate_quiz_safe(topic, num_questions)
    
    # Step 4: Display the quiz
    if output_format == 'j':
        print_json_quiz(quiz)
    else:
        print_quiz(quiz)
        
        # Also offer to show JSON
        show_json = input("\n[>] Show raw JSON output? (y/n): ").strip().lower()
        if show_json == 'y':
            print_json_quiz(quiz)


def main():
    """
    Main entry point with command-line argument support.
    
    Supports:
        --ingest <pdf_path>  : Ingest a PDF file
        --topic <topic>      : Generate quiz for specific topic
        --num <number>       : Number of questions (default: 5)
        --json               : Output as JSON instead of pretty format
    """
    parser = argparse.ArgumentParser(
        description="Quiz Generator System - RAG-powered educational quiz generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Interactive mode
  python main.py --ingest textbook.pdf     # Ingest a PDF
  python main.py --topic "photosynthesis"  # Generate quiz
  python main.py --topic "cells" --num 10  # Generate 10 questions
  python main.py --topic "DNA" --json      # Output as JSON
        """
    )
    
    parser.add_argument(
        "--ingest",
        type=str,
        metavar="PDF_PATH",
        help="Path to a PDF file to ingest into the vector database"
    )
    
    parser.add_argument(
        "--topic",
        type=str,
        help="Topic for quiz generation"
    )
    
    parser.add_argument(
        "--num",
        type=int,
        default=5,
        help="Number of questions to generate (default: 5)"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output quiz as JSON instead of pretty format"
    )
    
    args = parser.parse_args()
    
    # If no arguments provided, run interactive mode
    if len(sys.argv) == 1:
        interactive_mode()
        return
    
    # Handle ingestion
    if args.ingest:
        print_banner()
        print(f"\n[*] Ingesting PDF: {args.ingest}")
        try:
            ingest_pdf(args.ingest)
        except FileNotFoundError as e:
            print(f"\n[ERROR] {e}")
            sys.exit(1)
        except Exception as e:
            print(f"\n[ERROR] Ingestion failed: {e}")
            sys.exit(1)
        
        # If only ingesting, we're done
        if not args.topic:
            print("\n[OK] Ingestion complete. Run with --topic to generate quizzes.")
            return
    
    # Handle quiz generation
    if args.topic:
        print_banner()
        
        # Check if database exists
        if not vectorstore_exists():
            print("\n[ERROR] No vector database found.")
            print("   Please ingest a PDF first using: python main.py --ingest <pdf_path>")
            sys.exit(1)
        
        print(f"\n[...] Generating {args.num} questions about '{args.topic}'...")
        
        quiz = generate_quiz_safe(args.topic, args.num)
        
        if args.json:
            print_json_quiz(quiz)
        else:
            print_quiz(quiz)


if __name__ == "__main__":
    main()
