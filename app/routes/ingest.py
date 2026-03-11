from fastapi import APIRouter, Header, UploadFile,File
from pydantic import BaseModel
from app.rag.chunker import chunk_text
from app.rag.retriever import add_documents
from app.utils.pdf_parser import extract_text_from_pdf


router=APIRouter()

class IngestRequest(BaseModel):
    text:str

@router.post("/ingest")
def ingest_notes(data:IngestRequest):
    chunks=chunk_text(data.text)
    add_documents(chunks)

    return {
        "status":"success",
        "chunks_added":len(chunks)
    }

@router.post("/ingest/pdf")
async def ingest_pdf(file:UploadFile=File(...),x_session_id:str=Header(None)):
    session_id=x_session_id 
    print(f"Session ID in ingest route: {session_id}")

    file_bytes=await file.read()

    text = extract_text_from_pdf(file_bytes)

    chunks=chunk_text(text)

    add_documents(chunks,session_id)

    return {
        "status":"success",
        "filename":file.filename,
        "chunks_added":len(chunks)
    }