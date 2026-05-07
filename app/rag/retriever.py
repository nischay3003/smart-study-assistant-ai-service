import chromadb
from app.rag.embedder import get_embedding
from app.rag.hasher import chunk_exists, save_chunk_id
from app.rag.chunker import get_chunk_id


client=chromadb.PersistentClient(path="./chroma_db")
def get_collection(chat_id: str):
    collection = client.get_or_create_collection(name=f"notes_{chat_id}")
    print(f"Debug - Collection name: {collection.name}, Count: {collection.count()}")
    return collection

GLOBAL_COLLECTION= client.get_or_create_collection(name="global_notes")  # Separate collection for global docs



def keyword_score(query, doc):
    query_words = set(query.lower().split())
    doc_words = set(doc.lower().split())
    return len(query_words & doc_words)

def add_global_documents(
    chunks: list[str],
    file_hash: str = None,
    doc_id: str = None
):

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):

        chunk_id = get_chunk_id(chunk)

        # optional dedupe
        if chunk_exists(chunk_id, "global"):
            continue

        embedding = get_embedding(chunk)

        ids.append(chunk_id)
        embeddings.append(embedding)
        documents.append(chunk)

        metadatas.append({
            "chunk_id": chunk_id,
            "file_hash": file_hash,
            "doc_id": doc_id,
            "source": "global",
            "chunk_index": i
        })

        save_chunk_id(chunk_id, "global", doc_id)

    if ids:
        GLOBAL_COLLECTION.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )

    return len(ids)


def add_documents(chunks: list[str], chat_id: str = None, file_hash: str = None, doc_id: str = None):
    
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
            "doc_id": doc_id,
            "chunk_index": i
        })



        save_chunk_id(chunk_id, chat_id,doc_id)

    if ids:
        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )
    
    return len(ids)

def hybrid_retrieve(query, k: int = 3, chatId: str = None):
    collection = get_collection(chatId)

    # 🔹 semantic search (get more candidates)
    results = collection.query(
        query_embeddings=[get_embedding(query)],
        n_results=10
    )

    docs = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # 🔹 hybrid scoring
    scored = []
    for doc, dist in zip(docs, distances):
        semantic_score = 1 - dist   # higher is better
        keyword = keyword_score(query, doc)

        # 🔥 combine scores (tunable)
        final_score = (0.7 * semantic_score) + (0.3 * keyword)

        scored.append((doc, final_score))

    # 🔹 sort
    scored.sort(key=lambda x: x[1], reverse=True)

    return [doc for doc, _ in scored[:k]]

def retrieve_context(query:str,k:int=3,chatId:str=None):
    
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
    # print("Debug - Retrieved documents:", results.get("documents", [[]])[0])
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
