import os
from  google import genai
from dotenv import load_dotenv

load_dotenv()

client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def ask_llm(prompt:str)->str:
    try:
        response=client.models.generate_content(
                model=os.getenv("MODEL_NAME"),contents=prompt
            )
        return response.text
    except Exception as e:
        print("LLM error:",e)
        return "Sorry, I had trouble generating a response."
