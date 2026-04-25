import sqlite3

conn = sqlite3.connect("embeddings.db")
cur = conn.cursor()

try:
    cur.execute("ALTER TABLE files RENAME COLUMN session_storage TO chat_id")
    print("✅ files table updated")
except Exception as e:
    print("files table:", e)

try:
    cur.execute("ALTER TABLE chunks RENAME COLUMN session_storage TO chat_id")
    print("✅ chunks table updated")
except Exception as e:
    print("chunks table:", e)

conn.commit()
conn.close()