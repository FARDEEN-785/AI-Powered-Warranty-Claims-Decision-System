from sentence_transformers import SentenceTransformer

def load_embedding_model():
    """Load pre-trained sentence transformer model"""
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    print(" Embedding model loaded")
    return model


def embed_text(model, text: str):
    """Convert text to embedding vector (384 dimensions)"""
    embedding = model.encode(text)
    return embedding.tolist()  


if __name__ == "__main__":
    # Load model
    model = load_embedding_model()
    
    # Embed text
    text1 = "Screen is covered for 12 months"
    embedding1 = embed_text(model, text1)
    
    print(f"\nText: {text1}")
    print(f"Embedding length: {len(embedding1)}")
    print(f"First 5 values: {embedding1[:5]}")
    
    # Embed similar text
    text2 = "Glass damage coverage"
    embedding2 = embed_text(model, text2)
    
    print(f"\nText: {text2}")
    print(f"Embedding length: {len(embedding2)}")
    print(f"First 5 values: {embedding2[:5]}")