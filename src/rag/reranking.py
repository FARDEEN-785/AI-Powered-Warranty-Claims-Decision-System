from sentence_transformers import CrossEncoder
import numpy as np

# Load cross-encoder ONCE globally (expensive operation)
cross_encoder = CrossEncoder("cross-encoder/qnli-distilroberta-base")


def rerank_chunks(query: str, chunks: list, top_k: int = 3) -> list:
    """
    Rerank chunks using cross-encoder for better relevance.
    
    Args:
        query: The claim query (e.g., "Screen damage coverage")
        chunks: List of (chunk_text, similarity_score) tuples from FAISS
        top_k: Number of top results to return (default 3)
    
    Returns:
        List of reranked (chunk_text, score) tuples (top-k only)
    """
    
    # Step 1: Create pairs (query, chunk_text)
    pairs = [(query, chunk_text) for chunk_text, _ in chunks]
    #  FIXED: Extract chunk_text from tuple (chunk_text, similarity)
    
    # Step 2: Get relevance scores from cross-encoder
    scores = cross_encoder.predict(pairs)
    # Returns: array([4.2, 3.1, 2.5, 1.8, 1.2])
    
    # Step 3: Sort by score descending (highest relevance first)
    sorted_indices = np.argsort(scores)[::-1]
    #  FIXED: Use numpy argsort to get sorted indices
    
    # Step 4: Get top-k results with new scores
    reranked = [
        (chunks[i][0], float(scores[i]))  # (chunk_text, cross_encoder_score)
        for i in sorted_indices[:top_k]
    ]
    #  FIXED: Convert numpy float to Python float for JSON serialization
    
    return reranked


# TEST
# TEST
if __name__ == "__main__":
    from retrieval_node import vector_store, embedding_model, embed_text
    
    #  ADD CHUNKS FIRST!
    print("Adding sample policies to vector store...")
    sample_chunks = [
        "Screen is covered for 12 months. Max coverage: $1000.",
        "Battery is covered for 6 months. Max coverage: $500.",
        "Water damage is NOT covered.",
        "Physical damage is covered for 3 months.",
        "Accidental damage is covered for 6 months. Max $800."
    ]
    
    # Embed all chunks
    sample_embeddings = [embed_text(embedding_model, chunk) for chunk in sample_chunks]
    
    # Add to vector store
    vector_store.add_chunks(sample_chunks, sample_embeddings)
    print(f" Added {len(sample_chunks)} chunks\n")
    
    # Sample query
    query = "Is my screen covered?"
    query_embedding = embed_text(embedding_model, query)
    
    # Get top-5 from FAISS
    top_5 = vector_store.search(query_embedding, top_k=5)
    print("Before reranking (top-5 from FAISS):")
    for i, (chunk, score) in enumerate(top_5, 1):
        print(f"  {i}. [{score:.3f}] {chunk[:50]}...")
    
    # Rerank to top-3
    print("\nReranking with cross-encoder...")
    top_3 = rerank_chunks(query, top_5, top_k=3)
    
    print("\nAfter reranking (top-3 from Cross-Encoder):")
    for i, (chunk, score) in enumerate(top_3, 1):
        print(f"  {i}. [{score:.2f}] {chunk[:50]}...")