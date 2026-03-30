# from sentence_transformers import SentenceTransformer
 
# model=SentenceTransformer("all-MiniLM-L6-v2")

# def get_embedding(text:str)->list:
#     return model.encode(text).tolist()


from fastembed import TextEmbedding

model=TextEmbedding()

def get_embedding(text):
    return list(model.embed([text]))[0].tolist()