"""
Quiz Generation Module for Quiz Generator System
=================================================

This module handles the second phase of the RAG pipeline:
1. Retrieve relevant context from ChromaDB using LOCAL embeddings (FREE!)
2. Send context to Google Gemini LLM (only API call we make)
3. Generate structured JSON quiz with validated schema

HYBRID ARCHITECTURE:
- Retrieval: Uses LOCAL HuggingFace embeddings - FREE, UNLIMITED, no API calls
- Generation: Uses Google Gemini - Only 1 API call per quiz generation

RAG Flow - Generation Phase:
    User Query -> Local Embed -> Similarity Search -> Context -> Gemini LLM -> JSON Quiz
                     ^                                              ^
                     |                                              |
                 FREE! Local                               API Call (Quota)
"""

import os
import time
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ingest import load_vectorstore

# Load environment variables
load_dotenv()


# =============================================================================
# Pydantic Schema Definitions
# =============================================================================

class QuizQuestion(BaseModel):
    """Schema for a single quiz question."""
    question: str = Field(
        description="The quiz question text. Should be clear and based on the provided context."
    )
    options: List[str] = Field(
        description="Exactly 4 answer options. One must be correct, others should be plausible distractors.",
        min_length=4,
        max_length=4
    )
    correct_answer: str = Field(
        description="The correct answer. Must exactly match one of the options."
    )
    explanation: str = Field(
        description="Detailed explanation of why the correct answer is right. "
                    "This supports adaptive learning by helping students understand the concept."
    )


class QuizSchema(BaseModel):
    """Schema for the complete quiz output."""
    topic: str = Field(description="The topic/subject of the quiz.")
    questions: List[QuizQuestion] = Field(description="List of quiz questions.")
    context_available: bool = Field(
        default=True,
        description="Indicates if sufficient context was found to generate the quiz."
    )
    message: str = Field(
        default="",
        description="Optional message, especially when context is insufficient."
    )


# =============================================================================
# Quiz Generation Function
# =============================================================================

def generate_quiz(topic: str, num_questions: int = 5) -> dict:
    """
    Generate a structured quiz based on a topic using RAG.
    
    HYBRID ARCHITECTURE:
    - Step 1 (Retrieval): Uses LOCAL HuggingFace embeddings - FREE, no API quota used
    - Step 2 (Generation): Uses Google Gemini - Only API call, saves quota
    
    Args:
        topic: The topic/subject for which to generate quiz questions.
        num_questions: Number of questions to generate (default: 5).
    
    Returns:
        dict: Parsed quiz conforming to QuizSchema structure.
    
    Raises:
        ValueError: If API key is not configured.
        FileNotFoundError: If vector store doesn't exist.
    """
    # Validate API key (only needed for Gemini, not for retrieval)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )
    
    print(f"[*] Searching for context related to: '{topic}'")
    
    # Step 1: Load vector store and retrieve context
    print("   [*] Loading local embeddings for retrieval (FREE!)...")
    vectorstore = load_vectorstore()
    
    # Handle generic topics for "Take Quiz" functionality
    generic_topics = ["general", "all", "summary", "anything", "random", "take quiz"]
    is_generic = topic.lower().strip() in generic_topics
    
    if is_generic:
        print("   [*] Generic quiz requested, retrieving diverse context...")
        # Get more documents for a broader quiz
        retriever = vectorstore.as_retriever(
            search_type="mmr",  # Maximum Marginal Relevance for diversity
            search_kwargs={"k": 6, "fetch_k": 20}
        )
        search_query = "important health and care information" # Broad query
    else:
        # Create standard retriever
        retriever = vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 4}
        )
        search_query = topic

    # Perform retrieval
    relevant_docs = retriever.invoke(search_query)
    print(f"   [OK] Retrieved {len(relevant_docs)} relevant chunks (LOCAL - $0 cost)")
    
    if not relevant_docs:
        print("[!] No relevant context found in the document database.")
        return {
            "topic": topic,
            "questions": [],
            "context_available": False,
            "message": "I cannot generate a quiz because your knowledge base is empty. "
                       "Please upload some articles or PDFs first."
        }

    
    # Combine retrieved chunks into context
    context = "\n\n---\n\n".join([doc.page_content for doc in relevant_docs])
    
    # Step 2: Set up JSON output parser
    parser = JsonOutputParser(pydantic_object=QuizSchema)
    format_instructions = parser.get_format_instructions()
    
    # Step 3: Create prompt template
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert educational quiz generator. Your task is to create 
high-quality multiple-choice quiz questions based ONLY on the provided context.

CRITICAL RULES:
1. Generate questions ONLY from the information in the provided context.
2. Do NOT use any external knowledge.
3. If the context doesn't contain enough information about the topic, set 'context_available' 
   to false and explain in the 'message' field.
4. Each question must have exactly 4 options with only ONE correct answer.
5. The 'correct_answer' must EXACTLY match one of the options.
6. Provide detailed explanations that help students learn and understand the concept.
7. Make distractors (wrong options) plausible but clearly incorrect based on the context.

{format_instructions}"""),
        ("human", """Based on the following context, generate {num_questions} quiz questions 
about the topic: "{topic}"

CONTEXT:
{context}

Remember:
- Use ONLY the information from the context above
- If the context doesn't adequately cover the topic, indicate this in your response
- Generate exactly {num_questions} questions if possible
- Make each explanation educational and detailed""")
    ])
    
    # Step 4: Initialize the LLM
    # This is the ONLY API call we make - saves quota!
    print("   [...] Generating quiz with Gemini (API call)...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # Latest available model
        google_api_key=api_key,
        temperature=0.3,
        convert_system_message_to_human=True
    )
    
    # Step 5: Create and execute the chain with retry logic
    chain = prompt | llm | parser
    
    result = invoke_with_retry(
        chain,
        {
            "topic": topic,
            "num_questions": num_questions,
            "context": context,
            "format_instructions": format_instructions
        }
    )
    
    print(f"   [OK] Generated quiz with {len(result.get('questions', []))} questions")
    print("[DONE] Quiz generation complete!")
    
    return result


def invoke_with_retry(chain, inputs, max_retries=3, initial_wait=30):
    """
    Invoke a LangChain chain with retry logic for rate limit errors.
    
    Args:
        chain: The LangChain chain to invoke.
        inputs: The inputs to pass to the chain.
        max_retries: Maximum number of retry attempts.
        initial_wait: Initial wait time in seconds (doubles each retry).
    
    Returns:
        The result from the chain invocation.
    
    Raises:
        Exception: If all retries are exhausted.
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return chain.invoke(inputs)
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit error
            if "429" in error_msg or "resource_exhausted" in error_msg or "quota" in error_msg:
                last_exception = e
                
                if attempt < max_retries:
                    wait_time = initial_wait * (2 ** attempt)
                    print(f"   [!] Rate limit hit. Waiting {wait_time}s before retry {attempt + 1}/{max_retries}...")
                    time.sleep(wait_time)
                else:
                    raise Exception(
                        f"Google API quota exceeded after {max_retries} retries. "
                        f"Please wait a few minutes and try again, or check your API quota at "
                        f"https://ai.google.dev/gemini-api/docs/rate-limits"
                    )
            else:
                raise e
    
    raise last_exception


def generate_quiz_safe(topic: str, num_questions: int = 5) -> dict:
    """
    Safe wrapper for generate_quiz that handles all exceptions gracefully.
    
    Args:
        topic: The topic/subject for which to generate quiz questions.
        num_questions: Number of questions to generate (default: 5).
    
    Returns:
        dict: Either the generated quiz or an error response.
    """
    try:
        return generate_quiz(topic, num_questions)
    except FileNotFoundError as e:
        return {
            "topic": topic,
            "questions": [],
            "context_available": False,
            "message": f"Database error: {str(e)}"
        }
    except ValueError as e:
        return {
            "topic": topic,
            "questions": [],
            "context_available": False,
            "message": f"Configuration error: {str(e)}"
        }
    except Exception as e:
        return {
            "topic": topic,
            "questions": [],
            "context_available": False,
            "message": f"An unexpected error occurred: {str(e)}"
        }


if __name__ == "__main__":
    import json
    import sys
    
    topic = sys.argv[1] if len(sys.argv) > 1 else "machine learning"
    num_q = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    
    print(f"\n{'='*60}")
    print(f"Generating quiz on: {topic}")
    print(f"Number of questions: {num_q}")
    print(f"{'='*60}\n")
    
    quiz = generate_quiz_safe(topic, num_q)
    print("\n" + "="*60)
    print("GENERATED QUIZ:")
    print("="*60)
    print(json.dumps(quiz, indent=2))
