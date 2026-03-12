print("Starting AI Service...AI Study Assistant is now running on http://localhost:8000")
from fastapi import FastAPI
from dotenv import load_dotenv
import os
from app.routes.ask import router as ask_router
from app.routes.quiz import router as quiz_router
from app.routes.ingest import router as ingest_router
load_dotenv()

app = FastAPI(title="AI Study Assistant")

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(quiz_router)




