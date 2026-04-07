from embeddings import load_embedding_model, embed_text
from vector_store import FAISSVectorStore
from reranking import rerank_chunks
from database import get_db

# Load model ONCE globally
embedding_model = load_embedding_model()

# Initialize vector store ONCE globally
vector_store = FAISSVectorStore(embedding_dim=384)

# Get database instance
db = get_db()


def retrieval_node(state: dict) -> dict:
    """
    RAG Retrieval Node - retrieves relevant policy chunks from vector store.
    
    Input: state with 'claim' (warranty claim)
    Output: state with 'retrieved_chunks' (top-5 similar policies)
    """
    
    # Step 1: Extract claim text
    claim_text = state['claim'].claim_type
    if state['claim'].description:
        claim_text += f" {state['claim'].description}"
    
    # Step 2: Embed the claim
    query_embedding = embed_text(embedding_model, claim_text)
    
    # Step 3: Search vector store for top-5 similar chunks
    top_5_retrieved = vector_store.search(query_embedding, top_k=5)

     # Step 4: RERANKING - Rerank to top-3 (accurate)
    top_3_reranked = rerank_chunks(claim_text, top_5_retrieved, top_k=3)
    
    # Step 4: Log the retrieval action
    db.log_action(
        claim_id=state.get('claim_id', 'UNKNOWN'),
        node_name="retrieval_node",
        action=f"Retrieved 5 chunks, reranked to top 3",
        status="SUCCESS",
        input_data={"claim_type": state['claim'].claim_type},
        output_data={
            "chunks_retrieved": 5,
            "chunks_after_reranking": len(top_3_reranked),
            "reranked_scores": [float(round(score, 2)) for _, score in top_3_reranked]
        }    
    )
    
    # Step 5: Add retrieved chunks to state
    state['retrieved_chunks'] = top_3_reranked
    
    # Step 6: Return updated state
    return state


# TEST
if __name__ == "__main__":
    from models import ClaimRequest
    
    # Create test state
    state = {
        'claim_id': 'CLAIM-TEST123',
        'claim': ClaimRequest(
            customer_name="John Doe",
            claim_type="Screen Damage",
            amount=500.0,
            description="Cracked phone screen"
        ),
        'policy': None,
        'decision': None,
        'reason': None
    }
    
    # Add sample chunks to vector store
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
    
    # Run retrieval + reranking node
    print("\nRunning retrieval_node with reranking...")
    result = retrieval_node(state)
    
    # Check results
    if 'retrieved_chunks' in result:
        chunks = result['retrieved_chunks']
        print(f"\n✅ Retrieved & Reranked {len(chunks)} chunks:")
        for i, (chunk, score) in enumerate(chunks, 1):
            print(f"  {i}. [{score:.2f}] {chunk[:50]}...")
    else:
        print("❌ No chunks retrieved")