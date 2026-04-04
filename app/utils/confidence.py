def estimate_confidence(retrieved_docs:list[str],eval_score:int)->str:

    """
     Very simple heristic for now.
     Later we can improve.
    """

    if not retrieved_docs:
        return "low"
    
    total_len=sum(len(d) for d in retrieved_docs)

    if total_len>800:
        base= "high"
    elif total_len>300:
        base= "medium"
    else:
        base= "low"
    

    if eval_score >= 8:
        if base == "medium":
            return "high"
        return base

    elif eval_score <= 4:
        if base == "high":
            return "medium"
        return "low"

    return base
    