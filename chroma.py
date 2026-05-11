import chromadb

client = chromadb.PersistentClient(path="./path/to/your/chroma_db")


collection = client.get_collection(name="global_notes")


results = collection.get(include=["documents", "metadatas"])
print(results)   