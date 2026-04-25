import hashlib
from app.rag.db_setup import conn, cur

def save_file_hash(file_hash: str, chat_id: str,file_id:str):
    cur.execute("INSERT OR IGNORE INTO files (chat_id, file_hash,,file_id) VALUES (?, ?,?)", (chat_id, file_hash,file_id))
    conn.commit()

def check_if_file_exists(file_hash: str, chat_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM files WHERE chat_id=? AND file_hash=?",
        (chat_id, file_hash)
    )
    return cur.fetchone() is not None

def chunk_exists(chunk_id: str, chat_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM chunks WHERE chat_id=? AND chunk_id=?",
        (chat_id, chunk_id)
    )
    return cur.fetchone() is not None

def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def save_chunk_id(chunk_id: str, chat_id: str):
    cur.execute(
        "INSERT OR IGNORE INTO chunks (chat_id, chunk_id) VALUES (?, ?)",
        (chat_id, chunk_id)
    )
    conn.commit()
