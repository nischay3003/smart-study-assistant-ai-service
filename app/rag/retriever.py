import chromadb
from app.rag.embedder import get_embedding
from app.rag.hasher import chunk_exists, save_chunk_id
from app.rag.chunker import get_chunk_id
import uuid

client=chromadb.PersistentClient(path="./chroma_db")
def get_collection(session_id: str):
    collection = client.get_or_create_collection(name=f"notes_{session_id}")
    print(f"Debug - Collection name: {collection.name}, Count: {collection.count()}")
    return collection


def add_documents(chunks: list[str],session_id:str=None,file_hash:str=None):
    
    if(session_id is None):
        session_id="default"
    collection=get_collection(session_id)

    ids = []
    embeddings = []
    documents=[]
    metadatas=[]


    for i,chunk in enumerate(chunks):
        chunk_id=get_chunk_id(chunk)
        
        if chunk_exists(chunk_id, session_id):
            print(f"Debug - Skipping duplicate chunk: {chunk_id}")
            continue

        embedding=get_embedding(chunk)

        ids.append(chunk_id)
        embeddings.append(embedding)
        documents.append(chunk)

        metadatas.append({
            "chunk_id": chunk_id,
            "file_hash": file_hash,
            "session_id": session_id,
            "chunk_index": i
        })



        save_chunk_id(chunk_id, session_id)

    if ids:
        collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=ids
        )
    
    return len(ids)

def retrieve_context(query:str,k:int=4,session_id:str=None):
    
    q_emb=get_embedding(query)
    # print("Debug - Query embedding:", q_emb)
    collection=get_collection(session_id)
    
    #error handling query results
    print("Debug -query session_id:", session_id)
    print("Debug - collection name in retrieve_context:", collection.name)
    results=collection.query(
        query_embeddings=[q_emb],
        n_results=k
    )
    # print("Debug - Raw query results:", results)
    print("Debug - Retrieved documents:", results.get("documents", [[]])[0])
    docs=results.get("documents",[[]])[0]
    return docs

