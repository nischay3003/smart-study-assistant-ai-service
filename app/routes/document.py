from fastapi import APIRouter, Header, UploadFile, File, Form
from pydantic import BaseModel
from app.rag.chunker import chunk_text, get_chunk_id
from app.rag.retriever import add_documents
from app.utils.pdf_parser import extract_text
from app.rag.hasher import check_if_file_exists, get_file_hash, save_file_hash, get_file_hash_from_doc_id, delete_file_entry
from app.rag.retriever import get_collection, add_global_documents
from app.rag.retriever import client

router=APIRouter()
GLOBAL_COLLECTION= client.get_or_create_collection(name="global_notes")  # Separate collection for global docs

class IngestRequest(BaseModel):
    text:str

# @router.post("/document/ingest")
# def ingest_notes(data:IngestRequest):
#     chunks=chunk_text(data.text)
#     add_documents(chunks)

#     return {
#         "status":"success",
#         "chunks_added":len(chunks)
#     }


@router.post("/doc/ingest")
async def ingest_file(file:UploadFile=File(...),x_chat_id:str=Header(None), x_doc_id:str=Header(None)):
    chat_id=x_chat_id 
    doc_id=x_doc_id
    print(f"Chat ID in ingest route: {x_chat_id}")
    print(f"Doc ID in ingest route: {x_doc_id}")


    

    if not doc_id:
        return {"status": "error", "message": "doc_id is required"}

    file_bytes=await file.read()

    file_hash=get_file_hash(file_bytes)

    if check_if_file_exists(file_hash, chat_id):
        return {
            "status":"duplicate",
            "message":"This file has already been ingested for this chat."
        }
    
    save_file_hash(file_hash, chat_id, doc_id)
  

    

    text = extract_text(file_bytes, file)

    chunks=chunk_text(text)

    chunks_added=add_documents(chunks,chat_id,file_hash, doc_id)

    return {
        "status":"success",
        "filename":file.filename,
        "file_type": file.filename.split(".")[-1],
        "chunks_added":chunks_added,
        "file_hash":file_hash
    }


@router.post("/doc/admin/ingest")
async def ingest_global_doc(

    file: UploadFile = File(None),

    rawText: str = Form(None),

    title: str = Form(None),

    category: str = Form(None),

    description: str = Form(None),

    x_doc_id: str = Header(None)

):

    try:

        doc_id = x_doc_id

        if not doc_id:
            return {
                "status": "error",
                "message": "doc_id required"
            }

        # 🔥 either file or raw text
        if not file and not rawText:
            return {
                "status": "error",
                "message": "file or rawText required"
            }

        chat_id = "global"

        text = ""

        file_hash = ""

        # 🔥 FILE MODE
        if file:

            file_bytes = await file.read()

            file_hash = get_file_hash(file_bytes)

            if check_if_file_exists(file_hash, chat_id):
                return {
                    "status": "duplicate",
                    "message": "File already exists"
                }

            text = extract_text(file_bytes, file)

        # 🔥 RAW TEXT MODE
        else:

            text = rawText

            file_hash = get_file_hash(
                rawText.encode()
            )

        # 🔥 save hash
        save_file_hash(
            file_hash,
            chat_id,
            doc_id
        )

        # 🔥 chunking
        chunks = chunk_text(text)

        chunks_added = add_global_documents(
            chunks,
            file_hash=file_hash,
            doc_id=doc_id
        )

        return {
            "status": "success",
            "title": title,
            "category": category,
            "description": description,
            "chunks_added": chunks_added,
            "file_hash": file_hash
        }

    except Exception as e:

        print("Global ingestion error:", e)

        return {
            "status": "error",
            "message": str(e)
        }
    
@router.delete("/doc/admin/delete")
async def delete_global_document(doc_id: str):

    try:

        chat_id = "global"

        file_hash = get_file_hash_from_doc_id(
            doc_id,
            chat_id
        )

        if not file_hash:
            return {
                "status": "error",
                "message": "Document not found"
            }

        collection = GLOBAL_COLLECTION

        # 🔥 delete embeddings
        collection.delete(
            where={
                "doc_id": doc_id
            }
        )

        # 🔥 delete sqlite entry
        delete_file_entry(
            doc_id,
            chat_id
        )

        return {
            "status": "success",
            "message": "Global document deleted"
        }

    except Exception as e:

        print("Global delete error:", e)

    return {
            "status": "error",
            "message": str(e)
        
    }
    
@router.delete("/doc/delete")
async def delete_document(doc_id: str, chat_id: str):
    print(f"Doc ID in delete Route: {doc_id}, Chat ID: {chat_id}")
    try:
        if not chat_id or not doc_id:
            return {"message": "Both chat_id and doc_id are required"}

        # Get file_hash from SQLite
        file_hash = get_file_hash_from_doc_id(doc_id, chat_id)
        if not file_hash:
            return {"message": "Document not found in database"}

        collection = get_collection(chat_id)
        
        # Delete from ChromaDB
        collection.delete(
            where={
                "$and": [
                    {"doc_id": doc_id},
                    {"chat_id": chat_id}
                ]
            }
        )

        # Delete from SQLite
        delete_file_entry(doc_id, chat_id)

        return {"message": "Document deleted successfully"}

    except Exception as e:
        return {"message": f"Error while deleting document: {str(e)}"}