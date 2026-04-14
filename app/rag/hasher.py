import hashlib
from app.rag.db_setup import conn, cur

def save_file_hash(file_hash: str, session_id: str):
    cur.execute("INSERT OR IGNORE INTO files (session_id, file_hash) VALUES (?, ?)", (session_id, file_hash))
    conn.commit()

def check_if_file_exists(file_hash: str, session_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM files WHERE session_id=? AND file_hash=?",
        (session_id, file_hash)
    )
    return cur.fetchone() is not None

def chunk_exists(chunk_id: str, session_id: str) -> bool:
    cur.execute(
        "SELECT 1 FROM chunks WHERE session_id=? AND chunk_id=?",
        (session_id, chunk_id)
    )
    return cur.fetchone() is not None

def get_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()

def save_chunk_id(chunk_id: str, session_id: str):
    cur.execute(
        "INSERT OR IGNORE INTO chunks (session_id, chunk_id) VALUES (?, ?)",
        (session_id, chunk_id)
    )
    conn.commit()
