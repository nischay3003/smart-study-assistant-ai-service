import sqlite3

conn = sqlite3.connect("embeddings.db")
cur = conn.cursor()

# 🔥 Drop old tables
cur.execute("DROP TABLE IF EXISTS files")
cur.execute("DROP TABLE IF EXISTS chunks")

print("🗑️ Old tables dropped")

# ✅ Recreate with new schema
cur.execute("""
CREATE TABLE files (
    chat_id TEXT,
    file_hash TEXT,
    PRIMARY KEY (chat_id, file_hash)
)
""")

cur.execute("""
CREATE TABLE chunks (
    chat_id TEXT,
    chunk_id TEXT,
    PRIMARY KEY (chat_id, chunk_id)
)
""")

conn.commit()
conn.close()

print("✅ Tables recreated with new schema")