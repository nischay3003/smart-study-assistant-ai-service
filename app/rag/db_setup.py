import sqlite3
conn=sqlite3.connect("embeddings.db",check_same_thread=False)
cur=conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    session_id TEXT,
    file_hash TEXT,
    PRIMARY KEY (session_id, file_hash)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chunks (
    session_id TEXT,
    chunk_id TEXT,
    PRIMARY KEY (session_id, chunk_id)
)
""")

conn.commit()