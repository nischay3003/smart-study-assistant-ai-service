def chunk_text(text:str,chunk_size:int=500,overlap:int=50):
    """
        We are using simple sliding window chunking .
        chunk_size: characters

        This helps in preserving the context....
    """

    chunks=[]
    start=0

    while start<len(text):
        end=start+chunk_size
        chunk=text[start:end]
        chunks.append(chunk)
        start+=chunk_size-overlap

    return chunks

import hashlib


def get_chunk_id(chunk: str) -> str:
    normalized = chunk.strip().lower()
    return hashlib.md5(normalized.encode("utf-8")).hexdigest()


