import chromadb
from app.rag.embedder import get_embedding
import uuid

client=chromadb.PersistentClient(path="./chroma_db")
def get_collection(session_id: str):
    collection = client.get_or_create_collection(name=f"notes_{session_id}")
    print(f"Debug - Collection name: {collection.name}, Count: {collection.count()}")
    return collection


def add_documents(chunks: list[str],session_id:str=None):
    ids = []
    embeddings = []
    if(session_id is None):
        session_id="default"
    collection=get_collection(session_id)


    for chunk in chunks:
        ids.append(str(uuid.uuid4()))  
        embeddings.append(get_embedding(chunk))

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=ids
    )

def retrieve_context(query:str,k:int=4,session_id:str=None):
    if(session_id is None):
        session_id="default"
    q_emb=get_embedding(query)
    collection=get_collection(session_id)
    print("Debug -query session_id:", session_id)
    print("Debug - collection name in retrieve_context:", collection.name)
    results=collection.query(
        query_embeddings=[q_emb],
        n_results=k
    )
    docs=results.get("documents",[[]])[0]
    return docs

