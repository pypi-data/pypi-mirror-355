from pinecone import Pinecone, ServerlessSpec
from pr_agent.settings import settings
from pr_agent.core.embedder import _get_model

def main():
    # initialize the Pinecone client
    pc = Pinecone(api_key=settings.PINECONE_API_KEY)
  
    # 2) determine dimension
    dim = _get_model().get_sentence_embedding_dimension()

    existing = pc.list_indexes().names()
    if settings.PINECONE_INDEX not in existing: 
        pc.create_index(
            name=settings.PINECONE_INDEX,
            dimension=dim,
            metric="cosine",    # or "euclidean"
            spec=ServerlessSpec(
                cloud="aws",      # or "gcp" if your env ends in “-gcp”
                region=settings.PINECONE_ENV
            )
        )   
        print("Pinecone index ready:", settings.PINECONE_INDEX)
    else:
        print(f"Pinecone index already exists: {settings.PINECONE_INDEX}")

if __name__ == "__main__":
    main()

