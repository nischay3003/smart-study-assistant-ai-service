def estimate_confidence(retrieved_docs:list[str])->str:

    """
     Very simple heristic for now.
     Later we can improve.
    """

    if not retrieved_docs:
        return "low"
    
    total_len=sum(len(d) for d in retrieved_docs)

    if total_len>800:
        return "high"
    elif total_len>300:
        return "medium"
    else:
        return "low"
    
    