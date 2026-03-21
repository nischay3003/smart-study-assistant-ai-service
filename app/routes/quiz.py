from fastapi import APIRouter
from pydantic import BaseModel
from app.llm.client import ask_llm
import json
router=APIRouter()

class QuizRequest(BaseModel):
    topic:str
    difficulty:str="easy"
    num_questions:int=3

QUIZ_PROMPT = """
You are a computer science quiz generator.

Generate multiple choice questions.

Rules:
- Output STRICT valid JSON only
- No extra text
- Each question must have 4 options
- Do NOT include markdown.
- Provide correct answer index (0-3)

Format:
{
  "questions": [
    {
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "answerIndex": 0
    }
  ]
}
"""

@router.post("/generate-quiz")
def generate_quiz(data:QuizRequest):
    print(f"DEBUG — Received quiz request: {data}")

    topic=data.get("topic")
    difficulty=data.get("difficulty") if data.get("difficulty") else "easy"
    num_questions=data.get("num_questions") if data.get("num_questions") else 5
    prompt=f"""
        {QUIZ_PROMPT}
        TOPIC: {topic}
        DIFFICULTY: {difficulty}
        NUMBER OF QUESTIONS:{num_questions}
    """
    raw=ask_llm(prompt)
    print("DEBUG — raw quiz response:\n", raw)

    try:
        # Remove markdown code blocks if present
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0].strip()
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0].strip()
        quiz_json=json.loads(raw)
    except Exception as e:
        print("DEBUG — JSON parsing error:", e)
        quiz_json={"questions":[]}

    return quiz_json