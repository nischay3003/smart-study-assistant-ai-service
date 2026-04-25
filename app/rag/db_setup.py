import sqlite3
conn=sqlite3.connect("embeddings.db",check_same_thread=False)
cur=conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS files (
    file_id TEXT,
    chat_id TEXT,
    file_hash TEXT,
           
    PRIMARY KEY (chat_id,file_id)
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS chunks (
    chat_id TEXT,
    chunk_id TEXT,
    PRIMARY KEY (chat_id, chunk_id)
)
""")

conn.commit()