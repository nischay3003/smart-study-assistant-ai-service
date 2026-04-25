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
You are a planning agent.

Your job is to convert a user query into a sequence of SIMPLE, ATOMIC steps.

--------------------------------
AVAILABLE ACTIONS:

1. search → retrieve information from notes
2. explain → explain using retrieved context
3. quiz → generate quiz
4. summarize → create final report

--------------------------------
STRICT RULES (MUST FOLLOW):

1. Each step MUST contain ONLY ONE action.
2. NEVER combine actions in one step.
3. ALWAYS separate retrieval and reasoning.

--------------------------------
MANDATORY PATTERNS:

IF user asks to EXPLAIN:
→ MUST output EXACTLY:
[
  "search <topic>",
  "explain <topic>"
]

IF user asks for QUIZ:
→ MUST include:
[
  "search <topic>",
  "quiz <topic>"
]

IF user asks for REPORT / ANALYSIS:
→ MUST output:
[
  "search <topic>",
  "search <subtopic if needed>",
  "explain <topic>",
  "summarize <topic>"
]

--------------------------------
STEP FORMAT RULES:

- ONLY use these formats:
  - "search <topic>"
  - "explain <topic>"
  - "quiz <topic>"
  - "summarize <topic>"

- DO NOT use:
  ❌ search_notes:
  ❌ explanations inside steps
  ❌ multiple actions in one step

--------------------------------
EXAMPLES:

User: explain dbms
Output:
{
  "steps": ["search dbms", "explain dbms"]
}

User: generate quiz on dbms
Output:
{
  "steps": ["search dbms", "quiz dbms"]
}

User: create report on dbms indexing
Output:
{
  "steps": [
    "search dbms indexing",
    "search types of indexing",
    "explain dbms indexing",
    "summarize dbms indexing"
  ]
}

--------------------------------

Output ONLY valid JSON:
{
  "steps": ["step1", "step2"]
}

DO NOT add explanation.
DO NOT add markdown.
DO NOT break format.
"""
EVAL_PROMPT = """
You are an evaluator.

Evaluate the AI response based on:

1. Correctness
2. Completeness
3. Use of context

IMPORTANT RULES:
- "issues" MUST contain ONLY PROBLEMS.
- If there are no problems → return empty list [].
- DO NOT include positive statements in issues.

Return ONLY JSON:

{
  "score": 1-10,
  "issues": ["only real problems"],
  "verdict": "good / average / bad"
}
"""
import re

def evaluate_response(query, response,context):
    prompt=f"""

    {EVAL_PROMPT}
    Context:
    {context}
    Response:
    {response}
    """

    res = retry_llm_call(prompt)
    print("Evaluation LLM response:", res)
    print("Type of evaluation response:", type(res))
    try:
        evaluation = clean_json(res)

        # ✅ Ensure it's a dict
        if not isinstance(evaluation, dict):
            raise ValueError("Parsed evaluation is not a dict")

        return evaluation

    except Exception as e:
        print("Evaluation JSON Error:", res)

        # ✅ Always return consistent structure
        return {
            "score": None,   # IMPORTANT: use None instead of 5
            "issues": ["Could not parse evaluation response"],
            "verdict": "fallback"
        }
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
def map_step(step):
    step = step.lower()

    if "search" in step:
        return "search"

    elif "quiz" in step:   # ✅ move this ABOVE explain (priority)
        return "quiz"

    elif "explain" in step or "explanation" in step:
        return "explain"

    elif "report" in step or "summarize" in step:
        return "report"

    return "unknown"

def create_plan(query):
    print("Creating plan for query:", query)
    response = retry_llm_call(PLANNER_PROMPT + "\nUser Query: " + query)
    print("Planner LLM response:", response)

    parse_result = safe_json_parse(response)
    if parse_result and "steps" in parse_result:
        print("Parsed plan steps:", parse_result["steps"])
        return parse_result["steps"]
    else:
        print("Failed to parse plan, returning empty steps.")
        return []

def execute_tool(tool_name, input_data, chatId,context):
    print(f"Executing tool: {tool_name} with input: {input_data} for session: {chatId}")
    if tool_name == "search":
        retrieved_context= retrieve_context(query=input_data, chatId=chatId)
        seen = set()
        unique = []

        for doc in retrieved_context:
            if doc not in seen:
                unique.append(doc)
                seen.add(doc)

        retrieved_context = unique
        if(isinstance(retrieved_context,list)):
            context.extend(retrieved_context)
        else:
            context.append(retrieved_context)
        print("Context after search:", context)
        return retrieved_context
    elif tool_name == "explain":
        # res=retrieve_context(input_data, session_id=session_id)
        # context.extend[res]
            # final_output.extend(result)
            # print("Context retrieved for explanation:", result)

            
        print("Context for explanation:", context)
        prompt=f"""
                    Explain clearly using provided context only.
                    {context}
                    Explain:
                """ 
        response = retry_llm_call(prompt)
        print("Explanation response:", response)
            

        return response
    elif tool_name == "quiz":
        response = generate_quiz(input_data)
        print("Quiz generated:", response)
        # final_output.extend(response["questions"])
        # print("final_output after quiz generation:", final_output)
        return response
    elif tool_name == "report":
        prompt=f"""
            Create a structured report using the context below.

            Context:
            {context}

            
            """
        response = retry_llm_call(prompt)
        return response
    else:
        raise ValueError("Unknown tool: " + tool_name)
    

def execute_plan(steps, chatId):
    final_output = []
    context = []
    print("Chat ID in execute_plan:", chatId)
    for step in steps:
        print("Executing step:", step)

        action=map_step(step)
        print("Mapped action:", action)

        response=safe_tool_call(action, step, chatId,context)

        # handle error fallback
        if response == []:
            print("Tool failed, skipping step")
            continue

        if action !="search":
            if isinstance(response, list):
                final_output.extend(response)
            else:
                final_output.append(response)

        


        # if action=="search":
        #     result = retrieve_context(step, session_id=session_id)
        #     context.extend(result)
            

        # elif action=="explain":
        #     # retrieved_context=retrieve_context(step, session_id=session_id)
        #     # context.extend(retrieved_context)

        #     # final_output.extend(result)
        #     # print("Context retrieved for explanation:", result)

            
        #     print("Context for explanation:", context)
        #     prompt=f"""
        #             Explain clearly using provided context only.
        #             {context}
        #             Explain:
        #         """ 
        #     response = ask_llm(
        #         prompt
        #     )
        #     print("Explanation response:", response)
        #     final_output.append(response)

        # elif action=="quiz":
        #     response = generate_quiz(step)
        #     print("Quiz generated:", response)
        #     final_output.extend(response["questions"])
        #     print("final_output after quiz generation:", final_output)

        # elif action=="report":
        #     prompt=f"""
        #     Create a structured report using the context below.

        #     Context:
        #     {context}

            
        #     """
        #     response = ask_llm(prompt)
        #     final_output.append(response)

    return {"answer":final_output,
            "context":context}
import json


def clean_json(res):
    try:
        # Extract JSON block if wrapped in text
        match = re.search(r'\{.*\}', res, re.DOTALL)
        if match:
            res = match.group(0)

        return json.loads(res)

    except Exception as e:
        print("clean_json failed:", res)
        raise e

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
        return cleaned

    except Exception as e:
        print("Verifier JSON Error:", res)

        # fallback (VERY IMPORTANT)
        return {
                "complete": True,
                "missing": []
            }
    

def retry_llm_call(prompt, retries=2):
    for i in range(retries):
        try:
            response = ask_llm(prompt)

            if isinstance(response, str) and response.strip():
                return response

            if hasattr(response, "text") and response.text.strip():
                return response.text

        except Exception as e:
            print(f"Retry {i+1} failed:", e)

    return "ERROR: LLM failed"

def safe_json_parse(text):
    try:
        parsed = parse_llm_json(text)
        return parsed if parsed else {"steps": []}
    except Exception:
        return {
            "steps":[]
        }

def safe_tool_call(tool_name, input_data, chatId,context):
    try:
        return execute_tool(tool_name, input_data, chatId,context)
    except Exception as e:
        print("Tool error:", e)
        return []


def handle_query(query, chat_id):
    print("Handling query with planning agent...")
    print("Chat ID in handle_query:", chat_id)
    plan = create_plan(query)
    print("Generated Plan:", plan)

    execution_result = execute_plan(plan, chat_id)
    result=execution_result["answer"]
    context=execution_result["context"]
    verification=verify_response(query,result)

    if not verification["complete"]:
        print("Missing:", verification["missing"])

        # Fix by re-running missing steps
        print("Re-running missing steps...")
        fix_steps = verification["missing"]
        print("Steps to fix:", fix_steps)
        fix_result = execute_plan(fix_steps, chat_id)
        print("Final result after verification and fixing:", fix_result)
        if isinstance(result, list):
            result.extend(fix_result["answer"])
        else:
            result = str(result) + "\n" + str(fix_result["answer"])
        

    evaluation = evaluate_response(query, result, context)
    print("Evaluation:", evaluation)
    # evaluation={
    # "score": 10,
    # "issues": [],
    # "verdict": "good"
    # }


    return {"answer": result, "context": context ,"evaluation": evaluation}
