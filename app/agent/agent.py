from app.rag.retriever import retrieve_context
from app.routes.quiz import generate_quiz


# def generate_quiz_tool(topic, difficulty="easy", questions=5):
#     return generate_quiz({
#         "topic": topic,
#         "difficulty": difficulty,
#         "questions": questions
#     })

tools={
    "search_notes":retrieve_context,
    "generate_quiz":generate_quiz
}

SYSTEM_PROMPT = """
You are an AI Study Assistant Agent.

You MUST follow instructions EXACTLY.

----------------------------------------

TOOLS:

1. search_notes(query)
2. generate_quiz(topic)

----------------------------------------

DECISION RULES:

- If question is about study topics → use search_notes
- If user asks for quiz → use generate_quiz

----------------------------------------

CRITICAL OUTPUT RULES:

1.
    a.)If using a tool:
        → Return ONLY JSON
        → NO explanation
        → NO extra text
        → NO markdown
        → NO code block

        Correct format ONLY:

        {
        "tool": "search_notes",
        "arguments": {
            "query": "..."
        }
        }
    b.)TOOLS SECTION:

    generate_quiz(data)

    Where data must be:

    {
    "topic": "...",
    "difficulty": "easy/medium/hard",
    "questions": number_of_questions
    }   

    AND JSON FORMAT SHOULD BE:
        {
    "tool": "generate_quiz",
    "arguments": {
        "data": {
        "topic": "DBMS",
        "difficulty": "easy",
        "questions": 5
        }
    }
    }


2. If NOT using a tool:
   → Return ONLY final answer (plain text)
   → No JSON

----------------------------------------

FORBIDDEN:

- Do NOT say "I will..."
- Do NOT explain your reasoning
- Do NOT wrap JSON in ```json
- Do NOT add text before or after JSON

----------------------------------------

AFTER TOOL:

- Use result
- Give final answer
- STOP
"""
import json
from app.llm.client import ask_llm
from app.routes.ask import parse_llm_json
def run_agent(question, chat_history=[]):

    memory = {}

    prompt = f"""
{SYSTEM_PROMPT}

Previous conversation:
{chat_history}

Question:
{question}
"""

    for _ in range(5):  # prevent infinite loop

        response = ask_llm(prompt)
        parsed = parse_llm_json(response)

        print("DEBUG response:", response)

        # If no JSON → final answer
        if not parsed:
            return response

        tool_name = parsed.get("tool")
        args = parsed.get("arguments", {})

        # Safety fix
        if isinstance(args, str):
            args = {"query": args}

        print("DEBUG tool:", tool_name)
        print("DEBUG args:", args)

        # Stop condition
        if not tool_name or tool_name=="":
            return response
        
        if tool_name in memory:
            return str(memory[tool_name])

        if tool_name in tools:

            result = tools[tool_name](**args)

            print("DEBUG result:", result)

            # Store in memory
            memory[tool_name] = result

            # Feed structured result back
            prompt += f"""

            You already used the tool: {tool_name}

            Here is the result:
            {result}

            Now you MUST give the FINAL ANSWER.

            STRICT RULES:
            - DO NOT call any tool again
            - DO NOT return JSON
            - ONLY return the final answer
            """

        else:
            return "Invalid tool"

    return "Max iterations reached"