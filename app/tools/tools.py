"""
LangChain tool wrappers for study assistant operations.

Exposes ChromaDB retrieval and quiz generation as @tool-decorated functions
that can be bound to LLMs and used by LangGraph agents.
"""

from langchain_core.tools import tool
from typing import List, Dict, Any
from app.rag.retriever import hybrid_retrieve
from app.routes.quiz import generate_quiz
from langchain_core.runnables import RunnableConfig


@tool
def search_notes(query: str, config: RunnableConfig = None) -> List[Dict[str, Any]]:
    """
    Search through ingested study notes using hybrid (semantic + keyword) retrieval.
    
    Args:
        query: The search question or phrase
        config: Runtime configuration (automatically passed by LangGraph) - contains chat_id
    
    Returns:
        List of document chunks with 'content', 'source', and 'score' fields
    """
    # Extract chat_id from config if available
    chat_id = "default"
    if config and "configurable" in config:
        chat_id = config["configurable"].get("thread_id", "default")
    
    print(f"[Tool: search_notes] query='{query}' chat_id='{chat_id}'")
    
    try:
        # Returns list of dicts with 'content', 'metadata', 'score'
        results = hybrid_retrieve(query=query, k=5, chatId=chat_id)
        print(f"[Tool: search_notes] Found {len(results)} results")
        return results if results else []
    except Exception as e:
        print(f"[ERROR] search_notes failed: {e}")
        return []


@tool  
def generate_quiz_tool(
    topic: str, 
    difficulty: str = "medium", 
    num_questions: int = 5,
    config: RunnableConfig = None
) -> Dict[str, Any]:
    """
    Generate a quiz on a specific topic from the study notes.
    
    Args:
        topic: The subject matter for quiz questions
        difficulty: 'easy', 'medium', or 'hard'
        num_questions: Number of questions to generate (1-10)
        config: Runtime configuration (contains chat_id for context)
    
    Returns:
        Dict with 'questions' list, 'topic', and 'difficulty'
    """
    # Extract chat_id if needed for quiz generation
    chat_id = "default"
    if config and "configurable" in config:
        chat_id = config["configurable"].get("thread_id", "default")
    
    print(f"[Tool: generate_quiz_tool] topic='{topic}' chat_id='{chat_id}'")
    
    try:
        # generate_quiz returns a dict with 'questions', 'topic', etc.
        quiz = generate_quiz(
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions
        )
        return quiz
    except Exception as e:
        print(f"[ERROR] generate_quiz_tool failed: {e}")
        return {"error": str(e), "questions": []}


# Tool registries for different agent types
ALL_TOOLS = [search_notes, generate_quiz_tool]
RAG_TOOLS = [search_notes]
QUIZ_TOOLS = [generate_quiz_tool]