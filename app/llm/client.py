import os
from  google import genai
from dotenv import load_dotenv



from oauthlib.uri_validate import query
import requests
import json



load_dotenv()

client=genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
import requests

USE_LOCAL = False

def ask_llm(contents):
    if USE_LOCAL:
        return ask_ollama(contents)
    else:
        return ask_openrouter(contents)
import time

def ask_ollama(contents):
    try:
        start_time = time.time()   # 🔥 start timer

        # existing code...
        if isinstance(contents, list):
            prompt = ""
            for msg in contents:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                prompt += f"{role.upper()}: {content}\n"
        else:
            prompt = str(contents)

        print("Prompt length:", len(prompt))

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "phi3:mini",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_predict": 80
                }
            },
            
        )

        end_time = time.time()   # 🔥 end timer

        print(f"⏱️ LLM Response Time: {end_time - start_time:.2f} seconds")

        if response.status_code != 200:
            print("Ollama error:", response.text)
            return None

        return response.json().get("response", "")

    except Exception as e:
        print("Ollama Error:", e)
        return None
def ask_openrouter(contents):
    start_time = time.time()   # 🔥 start timer
    try:
        messages = contents if isinstance(contents, list) else [{"role": "user", "content": str(contents)}]

        data = {
            "model": "nvidia/nemotron-3-super-120b-a12b:free",
            "messages": messages,
            "reasoning": {"enabled": True}
        }
        api_key = os.getenv("OPEN_ROUTER_API_KEY")
        if not api_key:
            raise ValueError("Missing OPEN_ROUTER_API_KEY")
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Planner"
            },
            json=data, # This is safer than json.dumps
            timeout=45
        )

        # DEBUG: Print the raw status and text if it's not JSON
        print(f"Before Response status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            return None
        print(f"After response status check: {response.status_code}")

        res = response.json()
        return res['choices'][0]['message']['content']

    except Exception as e:
            print(f"Python Error: {e}")
            return None
    
    finally:
        end_time = time.time()   # 🔥 end timer
        print(f"⏱️ LLM Response Time: {end_time - start_time:.2f} seconds")
    
# def ask_llm(contents, tools=None):
 #     try:
 #         if tools:
 #             response=client.models.generate_content(
 #                     model=os.getenv("MODEL_NAME"),contents=contents, tools=tools
 #                 )
 #             return response
 #         else:
 #             response=client.models.generate_content(
 #                     model=os.getenv("MODEL_NAME"),contents=contents
 #                 )
 #             return response.text
 #     except Exception as e:
 #         print("LLM error:",e)
 #         return "Sorry, I had trouble processing your request."
