from langchain.embeddings.base import Embeddings


class E5Embeddings(Embeddings):
    def __init__(self, model):
        self.model = model

    def embed_documents(self, texts):
        texts = [f"passage: {t}" for t in texts]
        return self.model.embed_documents(texts)

    def embed_query(self, text):
        return self.model.embed_query(f"query: {text}")
