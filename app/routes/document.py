from fastapi import APIRouter, Header, UploadFile,File
from pydantic import BaseModel
from app.rag.chunker import chunk_text, get_chunk_id
from app.rag.retriever import add_documents
from app.utils.pdf_parser import extract_text_from_pdf
from app.rag.hasher import check_if_file_exists, get_file_hash, save_file_hash,save_chunk_id, chunk_exists
from app.rag.retriever import get_collection

router=APIRouter()

class IngestRequest(BaseModel):
    text:str

@router.post("/document/ingest")
def ingest_notes(data:IngestRequest):
    chunks=chunk_text(data.text)
    add_documents(chunks)

    return {
        "status":"success",
        "chunks_added":len(chunks)
    }

@router.post("/doc/ingest/pdf")
async def ingest_pdf(file:UploadFile=File(...),x_chat_id:str=Header(None)):
    chat_id=x_chat_id 
    print(f"Chat ID in ingest route: {x_chat_id}")

    file_bytes=await file.read()

    file_hash=get_file_hash(file_bytes)

    if check_if_file_exists(file_hash, chat_id):
        return {
            "status":"duplicate",
            "message":"This file has already been ingested for this chat."
        }
    
    save_file_hash(file_hash, chat_id)
  

    

    text = extract_text_from_pdf(file_bytes)

    chunks=chunk_text(text)

    chunks_added=add_documents(chunks,chat_id,file_hash)

    return {
        "status":"success",
        "filename":file.filename,
        "chunks_added":chunks_added,
        "file_hash":file_hash
    }

@router.delete("/doc/delete")
async def delete_document(file_hash: str, chat_id: str = None):
    print("File Hash in delete Route: ",file_hash," Chat id in Delete route: ",chat_id)
    try:
        if chat_id is None or not chat_id :
            return {"message":"Chat_id is required"}

        collection = get_collection(chat_id)
        

        collection.delete(
            where={
                "$and": [
                    {"file_hash": file_hash},
                    {"chat_id": chat_id}
                ]
            }
        )

        return {"message": "Document deleted successfully"}

    except Exception as e:
        return {"message": f"Error while deleting document: {str(e)}"}