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