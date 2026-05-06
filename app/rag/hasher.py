import hashlib
from app.rag.db_setup import conn, cur

def save_file_hash(file_hash: str, chat_id: str, doc_id: str):
    cur.execute("INSERT OR IGNORE INTO files (chat_id, file_hash, doc_id) VALUES (?, ?, ?)", (chat_id, file_hash, doc_id))
    conn.commit()

def check_if_file_exists(file_hash: str, chat_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM files WHERE chat_id=? AND file_hash=?",
        (chat_id, file_hash)
    )
    return cur.fetchone() is not None

def get_file_hash_from_doc_id(doc_id: str, chat_id: str) -> str:
    cur.execute(
        "SELECT file_hash FROM files WHERE chat_id=? AND doc_id=?",
        (chat_id, doc_id)
    )
    result = cur.fetchone()
    return result[0] if result else None

def delete_file_entry(doc_id: str, chat_id: str):
    cur.execute(
        "DELETE FROM files WHERE chat_id=? AND doc_id=?",
        (chat_id, doc_id)
    )
    print(f"Deleted file entry for doc_id: {doc_id}, chat_id: {chat_id}")
    conn.commit()

def chunk_exists(chunk_id: str, chat_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM chunks WHERE chat_id=? AND chunk_id=?",
        (chat_id, chunk_id)
    )
    return cur.fetchone() is not None

def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def save_chunk_id(chunk_id: str, chat_id: str,doc_id:str):
    cur.execute(
        "INSERT OR IGNORE INTO chunks (chat_id, chunk_id,doc_id) VALUES (?, ?,?)",
        (chat_id, chunk_id,doc_id)
    )
    conn.commit()
