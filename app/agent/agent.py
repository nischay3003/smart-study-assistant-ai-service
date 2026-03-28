from app.rag.retriever import retrieve_context
from app.routes.quiz import QuizRequest, generate_quiz


# def generate_quiz_tool(topic, difficulty="easy", questions=5):
#     return generate_quiz({
#         "topic": topic,
#         "difficulty": difficulty,
#         "questions": questions
#     })
SYSTEM_PROMPT="""
You are an AI agent that can ONLY answer using tools.

You CANNOT answer from your own knowledge.

AVAILABLE TOOLS:
1. search_notes(query)
2. generate_quiz(topic)
3. NONE (if no tool is needed)

------------------------
MANDATORY RULES:

1. You MUST ALWAYS start with a Thought.
2. If the question involves notes → you MUST call search_notes FIRST.
3. You are NOT allowed to answer without using tools.
4. DO NOT skip tool usage.
5. DO NOT use your own knowledge.
6. DO NOT assume anything.

------------------------
FORMAT (STRICT — NO DEVIATION):

Thought: what you need to do
Action: search_notes OR generate_quiz
Action Input: exact input

------------------------

After tool response:

Observation: tool result

Then continue reasoning again using:

Thought:
Action:
Action Input:

------------------------

ONLY when ALL required steps are done:

Final Answer: (based ONLY on tool results)



------------------------
TOOL USAGE BOUNDARY:

- Each tool has a specific purpose:
  • search_notes → retrieve information
  • generate_quiz → create quiz ONLY if explicitly requested

- After using search_notes:
  → If the user ONLY asked for explanation,
     you MUST directly produce Final Answer.
  → DO NOT call generate_quiz.

- You MUST NOT use generate_quiz unless the user explicitly asks for a quiz.

- Once required information is retrieved,
  you MUST STOP calling tools.


IMPORTANT:

- If you skip tools → you are WRONG
- If you answer from knowledge → you are WRONG
- You MUST rely completely on tools


"""
import re
def parse_react_output(text):
    import re

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