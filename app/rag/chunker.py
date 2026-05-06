import re

def chunk_text(text, chunk_size=300, overlap=50):
    sentences = re.split(r'(?<=[.!?]) +', text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence
        else:
            chunks.append(current_chunk.strip())
            
            # 🔥 overlap: keep last part
            current_chunk = current_chunk[-overlap:] + " " + sentence

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

import hashlib


def get_chunk_id(chunk: str) -> str:
    normalized = chunk.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


