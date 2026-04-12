print("Starting AI Service...AI Study Assistant is now running on http://localhost:8000")
from fastapi import FastAPI,UploadFile,File
from dotenv import load_dotenv
import asyncio
import os
import whisper
from app.routes.ask import router as ask_router
from app.routes.quiz import router as quiz_router
from app.routes.ingest import router as ingest_router
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="AI Study Assistant")
model=whisper.load_model("base")



app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # your frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/speech-to-text")
async def speech_to_text(file:UploadFile=File(...)):
    
    try:
        with open("temp_audio.webm", "wb") as f:
            f.write(await file.read())
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
           None, lambda: model.transcribe("temp_audio.webm")
        )
        print("Transcription result:", result['text'])
        return {"text": result['text']}
    except Exception as e:
        print(f"Error during transcription: {e}")
        return {"error": "Transcription failed"}
    

app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(quiz_router)




