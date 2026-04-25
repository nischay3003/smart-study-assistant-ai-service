import chromadb
from app.rag.embedder import get_embedding
from app.rag.hasher import chunk_exists, save_chunk_id
from app.rag.chunker import get_chunk_id


client=chromadb.PersistentClient(path="./chroma_db")
def get_collection(chat_id: str):
    collection = client.get_or_create_collection(name=f"notes_{chat_id}")
    print(f"Debug - Collection name: {collection.name}, Count: {collection.count()}")
    return collection


def add_documents(chunks: list[str],chat_id:str=None,file_hash:str=None):
    
    if(chat_id is None):
        chat_id="default"
    collection=get_collection(chat_id)

    ids = []
    embeddings = []
    documents=[]
    metadatas=[]


    for i,chunk in enumerate(chunks):
        chunk_id=get_chunk_id(chunk)
        
        if chunk_exists(chunk_id, chat_id):
            print(f"Debug - Skipping duplicate chunk: {chunk_id}")
            continue

        embedding=get_embedding(chunk)

        ids.append(chunk_id)
        embeddings.append(embedding)
        documents.append(chunk)

        metadatas.append({
            "chunk_id": chunk_id,
            "file_hash": file_hash,
            "chat_id": chat_id,
            "chunk_index": i
        })



        save_chunk_id(chunk_id, chat_id)

    if ids:
        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids
        )
    
    return len(ids)

def retrieve_context(query:str,k:int=4,chatId:str=None):
    
    q_emb=get_embedding(query)
    # print("Debug - Query embedding:", q_emb)
    collection=get_collection(chatId)
    
    #error handling query results
    print("Debug -query chat_id:", chatId)
    print("Debug - collection name in retrieve_context:", collection.name)
    results=collection.query(
        query_embeddings=[q_emb],
        n_results=k
    )
    # print("Debug - Raw query results:", results)
    print("Debug - Retrieved documents:", results.get("documents", [[]])[0])
    docs=results.get("documents",[[]])[0]
    return docs

# def delete_document(file_hash: str, chat_id: str = None):
#     if chat_id is None:
#         chat_id = "default"

#     collection = get_collection(chat_id)

#     collection.delete(
#         where={
#             "file_hash": file_hash,
#             "chat_id":chat_id
#             }
#     )

#     return {"message": "Document deleted successfully"}
