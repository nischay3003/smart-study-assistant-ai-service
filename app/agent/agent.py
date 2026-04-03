from app.rag.retriever import retrieve_context
from app.routes.quiz import QuizRequest, generate_quiz


# def generate_quiz_tool(topic, difficulty="easy", questions=5):
#     return generate_quiz({
#         "topic": topic,
#         "difficulty": difficulty,
#         "questions": questions
#     })
SYSTEM_PROMPT = """
You are a Smart Study Assistant that ONLY answers using tools.
You CANNOT answer from your own knowledge.

AVAILABLE TOOLS:
1. search_notes(query) — retrieves information from the user's notes
2. generate_quiz(topic) — generates a quiz on a topic
3. NONE — only for greetings or unrelated conversation

------------------------
MANDATORY RULES:

1. ALWAYS start with a Thought.
2. If the user asks about a topic → call search_notes. Then give Final Answer. STOP.
3. If the user explicitly asks for a quiz → call generate_quiz. Then give Final Answer. STOP.
4. NEVER call generate_quiz unless the user uses words like "quiz", "test me", "make a quiz".
5. NEVER call more than ONE tool per response.
6. NEVER answer from your own knowledge.
7. NEVER chain tools together unless the user asks for both in the same message.

------------------------
STRICT FORMAT:

Thought: what you need to do
Action: search_notes OR generate_quiz OR NONE
Action Input: exact input

Observation: tool result

Thought: what the result means
Final Answer: response based ONLY on the Observation

------------------------
EXAMPLES:

User: "Explain photosynthesis"
Thought: User wants an explanation. I must search their notes. I will NOT generate a quiz.
Action: search_notes
Action Input: photosynthesis
Observation: <result>
Thought: I have the explanation. My job is done. I will NOT call any more tools.
Final Answer: Based on your notes, photosynthesis is...

---

User: "Quiz me on photosynthesis"
Thought: User explicitly asked for a quiz. I must call generate_quiz.
Action: generate_quiz
Action Input: photosynthesis
Observation: <quiz>
Thought: Quiz is ready. My job is done.
Final Answer: Here is your quiz...

---

User: "Explain photosynthesis and then quiz me"
Thought: User asked for both explanation AND quiz. I will search notes first.
Action: search_notes
Action Input: photosynthesis
Observation: <result>
Thought: Now I have the explanation. User also asked for a quiz so I call generate_quiz.
Action: generate_quiz
Action Input: photosynthesis
Observation: <quiz>
Thought: Both tasks done.
Final Answer: Here is the explanation... and here is your quiz...

---

User: "Hey!"
Thought: This is a greeting. No tool needed.
Action: NONE
Action Input: NONE
Final Answer: Hi! Ask me anything from your notes or say quiz me on a topic!

------------------------
REMEMBER:
- search_notes = explanation requests → STOP after Final Answer
- generate_quiz = ONLY when user says quiz/test me → STOP after Final Answer
- NEVER assume the user wants a quiz just because you explained a topic
"""
PLANNER_PROMPT = """
You are a planning agent for a Smart Study Assistant.

Your job is to create a minimal step-by-step plan based ONLY on what the user explicitly asked for.

AVAILABLE CAPABILITIES:
- search_notes: use when user asks about a topic or wants an explanation
- generate_quiz: use ONLY when user explicitly says "quiz", "test me", "make a quiz"

------------------------
STRICT PLANNING RULES:

1. ONLY include steps the user explicitly asked for.
2. NEVER add generate_quiz unless the user clearly asked for a quiz.
3. NEVER add extra steps to be helpful — do exactly what was asked, nothing more.
4. Keep the plan as short as possible — minimum steps needed.
5. Output ONLY valid JSON, no extra text.

------------------------
EXAMPLES:

User: "Explain Newton's laws"
{
  "steps": ["search_notes: Newton's laws"]
}

User: "Quiz me on Newton's laws"
{
  "steps": ["generate_quiz: Newton's laws"]
}

User: "Explain Newton's laws and quiz me"
{
  "steps": ["search_notes: Newton's laws", "generate_quiz: Newton's laws"]
}

User: "Hey!"
{
  "steps": []
}

------------------------
REMEMBER:
- Short plan = good plan
- Adding unrequested steps = wrong
- generate_quiz is NEVER assumed — it must be explicitly requested
"""

import re


def parse_react_output(text):


    if "Final Answer:" in text:
        final = text.split("Final Answer:")[-1].strip()
        return {"final": final}

    thought = re.search(r"Thought:\s*(.*)", text)
    action = re.search(r"Action:\s*(\w+)", text)
    action_input = re.search(r"Action Input:\s*(.*)", text)

    return {
        "thought": thought.group(1).strip() if thought else None,
        "action": action.group(1).strip() if action else None,
        "input": action_input.group(1).strip() if action_input else None
    }

tools={
    "search_notes":retrieve_context,
    "generate_quiz":generate_quiz
}

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
        print("LLM response:", response)
        print(str(_) + "th iteration")

        parsed = parse_react_output(response)
        print("Parsed LLM response:", parsed)


        if "final" in parsed:
            print("Final answer found, returning:", parsed["final"])
            return parsed["final"]
        
        action=parsed.get("action")
        action_input=parsed.get("input")


        if not action:
            return response
        
        if action in memory:
            prompt += "\nYou already used this tool. Do not repeat it.\n"
            continue
        if action=="NONE":
            continue

        print("Action to be done: ", action)
        if action =="search_notes":
            print("calling search_notes function")
            result = tools[action](query=action_input)
            print("search_notes called with query:", action_input)
        elif action =="generate_quiz":
            result = tools[action](action_input)
            print("generate_quiz called with input:", action_input)
        else :
            return "Invalid tool"
        
        memory[action] = result


      
        prompt += f"""

        Observation:
        {result}

        ----------------------------------------

        Now continue reasoning.

        Check:
        - Are ALL parts of the user question completed?

        If NOT:
        → continue with next step

        If YES:
        → return Final Answer
        """
    
    return "Max iterations reached"

def create_plan(query):
    print("Creating plan for query:", query)
    response = ask_llm(PLANNER_PROMPT + "\nUser Query: " + query)
    print("Planner LLM response:", response)

    parse_result = parse_llm_json(response)
    if parse_result and "steps" in parse_result:
        print("Parsed plan steps:", parse_result["steps"])
        return parse_result["steps"]
    else:
        print("Failed to parse plan, returning empty steps.")
        return []

def execute_plan(steps, session_id):
    final_output = []
    context = []

    for step in steps:
        print("Executing step:", step)

        # if "search" in step.lower():
        #     result = retrieve_context(step, session_id=session_id)
        #     final_output.append(result)

        if "search" in step.lower():
            retrieved_context = retrieve_context(step, session_id=session_id)
            # final_output.extend(result)
            # print("Context retrieved for explanation:", result)
            context = "\n".join(retrieved_context)
            print("Context for explanation:", context)
            prompt=f"""
                    Explain clearly using provided context only.
                    {context}
                    Explain:
                """ 
            response = ask_llm(
                prompt
            )
            print("Explanation response:", response)
            final_output.append(response)

        elif "quiz" in step.lower():
            response = generate_quiz(step)
            print("Quiz generated:", response)
            final_output.extend(response["questions"])
            print("final_output after quiz generation:", final_output)

    return {"answer":final_output,
            "context":context}
import json

def clean_json(text):
    text = text.strip()

    # remove ```json ``` if present
    if text.startswith("```"):
        text = text.split("```")[1]

    return text.strip()


def verify_response(query, response_text):
    prompt = f"""
        You are a verification agent.

        Check if the response fully answers the user query.

        Return ONLY valid JSON.
        Do NOT add explanation.
        Do NOT use markdown.

        Format:
        {{
        "complete": true or false,
        "missing": ["list of missing parts"]
        }}

        User Query:
        {query}

        Response:
        {response_text}

        If everything is correct:
        {{
        "complete": true,
        "missing": []
        }}
        """
    print("starting verification with prompt:", prompt)
    res = ask_llm(prompt)
    print("Verification LLM response:", res)
    import logging
    try:
        logging.basicConfig(level=logging.DEBUG)
        cleaned = clean_json(res)
        logging.debug(f"Cleaned verification response: {cleaned}")
        print("Cleaned verification response:", cleaned)
        return json.loads(cleaned)

    except Exception as e:
        print("Verifier JSON Error:", res)

        # fallback (VERY IMPORTANT)
        return {
                "complete": True,
                "missing": []
            }

def handle_query(query, session_id="default"):
    print("Handling query with planning agent...")
    plan = create_plan(query)
    print("Generated Plan:", plan)

    execution_result = execute_plan(plan, session_id)
    result=execution_result["answer"]
    context=execution_result["context"]
    verification=verify_response(query,result)

    if not verification["complete"]:
        print("Missing:", verification["missing"])

        # Fix by re-running missing steps
        fix_steps = verification["missing"]

        fix_result = execute_plan(fix_steps, session_id)

        result += "\n\n[FIXED PART]\n" + fix_result

    return {"answer": result, "context": context}