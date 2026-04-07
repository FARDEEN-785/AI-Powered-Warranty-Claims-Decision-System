import faiss
import numpy as np
from typing import List, Tuple

class FAISSVectorStore:

    def __init__(self, embedding_dim: int = 384):
        """Initialize FAISS index"""
        self.index = faiss.IndexFlatL2(embedding_dim)
        self.chunks = []  
        self.chunk_ids = []
        self.embedding_dim = embedding_dim


    def add_chunks(self, chunks: List[str], embeddings: List):
        """Add chunks and embeddings to index"""
       
        embedding_array = np.array(embeddings, dtype=np.float32)
        
        # Add to FAISS
        self.index.add(embedding_array)
        
       
        chunk_ids = [f"CHUNK-{i}" for i in range(len(chunks))]
        self.chunk_ids.extend(chunk_ids)
        
        # Store chunks
        self.chunks.extend(chunks)
        
        print(f" Added {len(chunks)} chunks to index")


    def search(self, query_embedding, top_k: int = 3) -> List[Tuple[str, float]]:
        """Search for top-k similar chunks"""
       
        query_array = np.array([query_embedding], dtype=np.float32)
        
        # Search FAISS
        distances, indices = self.index.search(query_array, top_k)
        
       
        results = []
        for distance, idx in zip(distances[0], indices[0]):
            similarity = 1 / (1 + distance) 
            chunk_text = self.chunks[idx]
            results.append((chunk_text, similarity))
        
        return results


    def get_stats(self) -> dict:
        """Get statistics about vector store"""
        return {
            "total_chunks": self.index.ntotal,
            "embedding_dim": self.embedding_dim,
            "index_type": "FAISS (L2 distance)"
        }


# TEST
if __name__ == "__main__":
    from embeddings import load_embedding_model, embed_text
    
    # Load model
    model = load_embedding_model()
    
    # Create vector store
    vs = FAISSVectorStore(embedding_dim=384)
    
    # Create chunks
    chunks = [
        "Screen is covered for 12 months. Max coverage: $1000.",
        "Battery is covered for 6 months. Max coverage: $500.",
        "Water damage is NOT covered.",
        "Physical damage is covered for 3 months."
    ]
    
    # Embed all chunks
    embeddings = [embed_text(model, chunk) for chunk in chunks]
    
    # Add to index
    vs.add_chunks(chunks, embeddings)
    
    # Print stats
    stats = vs.get_stats()
    print(f"\nVector store stats: {stats}")
    
    # Search
    query = "Is my screen covered?"
    query_embedding = embed_text(model, query)
    
    print(f"\nQuery: {query}")
    results = vs.search(query_embedding, top_k=2)
    
    print(f"Results:")
    for i, (chunk, similarity) in enumerate(results, 1):
        print(f"  {i}. [{similarity:.3f}] {chunk[:50]}...")