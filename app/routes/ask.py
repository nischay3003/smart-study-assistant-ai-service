from fastapi import APIRouter,Header
from pydantic import BaseModel
from app.llm.client import ask_llm
from app.rag.retriever import retrieve_context
from app.utils.confidence import estimate_confidence


router=APIRouter()

class AskRequest(BaseModel):
    question:str
    chat_history:list=[]

SYSTEM_PROMPT = """
You are a strict and helpful AI study assistant.

Your job is to answer the student's question using ONLY the provided context.

Rules:
- Answer ONLY using the provided context.
- If the answer is not present in the context, respond exactly with: "Not found in notes."
- Be concise and clear.
- Prefer bullet points when explaining concepts.
- Do not invent information.
- Extract the main academic topic of the question (1-3 words).
Return ONLY raw JSON.
Do NOT wrap the JSON in markdown or code blocks.

Format:

{
 "answer": "...",
 "topic": "..."
}
"""

import json
import re

def parse_llm_json(raw_response: str):
    try:
        cleaned = re.sub(r"```json|```", "", raw_response).strip()
        return json.loads(cleaned)
    except Exception as e:
        print("JSON parsing failed:", e)
        return None


def guess_topic(question: str) -> str:
    q = question.lower()

    if "normalization" in q:
        return "normalization"
    if "acid" in q:
        return "acid"
    if "index" in q:
        return "indexing"
    if "transaction" in q:
        return "transactions"

    return "general"


def format_chat_history(history: list, max_turns: int = 3) -> str:
    if not history:
        return ""

    recent = history[-max_turns:]
    formatted = []

    for msg in recent:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        formatted.append(f"{role.upper()}: {content}")
    print("DEBUG — formatted chat history:\n", "\n".join(formatted))
    return "\n".join(formatted)


@router.post("/ask")
def ask_question(data:AskRequest,x_session_id:str=Header(None)):

    if not data.question or len(data.question.strip())<3:
        return {
            "answer":"Please provide a valid question.",
            "confidence":"low",
            "sources":[],
            "topic":"general"
        }

    print("Ask.py file", x_session_id)
    contexts = retrieve_context(data.question, k=4, session_id=x_session_id)

    print(f"[ASK] Question: {data.question}")
    print(f"[ASK] Retrieved chunks: {len(contexts)}")
    
    if not contexts:
        return {
            "answer":"Not found in notes.",
            "confidence":"low",
            "sources":[],
            "topic":guess_topic(data.question)
        }

    MAX_CONTEXT_CHARS=2000

    context_text="\n\n".join(contexts)[:MAX_CONTEXT_CHARS]
    topic=guess_topic(data.question)

    history_text = format_chat_history(data.chat_history)
    print ("history_text:\n", history_text)

    prompt=f"""
    {SYSTEM_PROMPT}

    Previous conversation:
    {history_text}

    Context:
    {context_text}

    Question:
    {data.question}

    """

    import json
    raw_response = ask_llm(prompt)

    parsed = parse_llm_json(raw_response)

    if parsed:
        answer = parsed.get("answer", "Not found in notes.")
        topic = parsed.get("topic", "general")
    else:
        answer = raw_response
        topic = "general"

    confidence = estimate_confidence(contexts)
    
    clean_sources = contexts[:2]  # top 2 only



    return {
        "answer":answer,
        "confidence":confidence,
        "sources":clean_sources,
        "topic": topic
    }