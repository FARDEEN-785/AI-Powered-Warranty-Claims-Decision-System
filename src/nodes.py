from models import AgentState, ClaimResult
from ingest import ingest_warranty
from database import get_db

db = get_db()

def ingest_node(state: AgentState) -> AgentState:
    pdf_path = state["pdf_path"]
    policy = ingest_warranty(pdf_path)
    return {"policy": policy}

def receive_claim_node(state: AgentState) -> AgentState:
    claim = state["claim"]
    print("\n" + "="*50)
    print("CLAIM RECEIVED")
    print(f"Customer: {claim.customer_name}")
    print(f"Claim Type: {claim.claim_type}")
    print(f"Amount: ${claim.amount}")
    print("="*50)
    return state

def check_coverage_node(state: AgentState) -> dict:
    """
    Check if claim is covered based on RETRIEVED policy chunks.
    """
    claim = state["claim"]
    retrieved_chunks = state.get('retrieved_chunks', [])
    days_since_purchase = state.get('days_since_purchase', 0)
    has_receipt = state.get('has_receipt', True)
    
    # Check 1: Valid amount
    if claim.amount <= 1.0:
        return {
            "decision": "REJECT",
            "reason": f"Invalid claim amount: ${claim.amount}"
        }
    
    # Check 2: Has receipt
    if not has_receipt:
        return {
            "decision": "REVIEW",
            "reason": "Original receipt required"
        }
    
    # Check 3: Using RAG chunks to determine coverage
    if retrieved_chunks:
        print("\n" + "="*50)
        print("CHECKING COVERAGE WITH RAG")
        print(f"Claim Type: {claim.claim_type}")
        print(f"Amount: ${claim.amount}")
        for i, (chunk, similarity) in enumerate(retrieved_chunks, 1):
            print(f"  {i}. [{similarity:.2f}] {chunk[:60]}...")
        print("="*50)
        
        # Search chunks for coverage info
        for chunk, _ in retrieved_chunks:
            chunk_lower = chunk.lower()
            claim_type_lower = claim.claim_type.lower()
            
            # Find matching chunk for claim type
            if claim_type_lower in chunk_lower:
                
                # Check 1: Is it excluded?
                if "not covered" in chunk_lower or "excluded" in chunk_lower:
                    return {
                        "decision": "REJECT",
                        "reason": f"{claim.claim_type} is NOT covered"
                    }
                
                # Check 2: Is it covered?
                if "covered" in chunk_lower:
                    
                    # Check 3: Checking expiration if mentioned
                    if "12 months" in chunk_lower:
                        if days_since_purchase > 365:
                            return {
                                "decision": "REJECT",
                                "reason": f"Warranty expired (day {days_since_purchase})"
                            }
                    elif "24 months" in chunk_lower:
                        if days_since_purchase > 730:
                            return {
                                "decision": "REJECT",
                                "reason": f"Warranty expired (day {days_since_purchase})"
                            }
                    
                    # Check 4: Check max amount 
                    import re
                    max_match = re.search(r'\$(\d+)', chunk)
                    
                    if max_match:
                        chunk_max = float(max_match.group(1))
                        if claim.amount > chunk_max:
                            return {
                                "decision": "REVIEW",
                                "reason": f"Amount (${claim.amount}) exceeds max (${chunk_max})"
                            }
                        # Amount is OK, approve
                        return {
                            "decision": "APPROVE",
                            "reason": f"{claim.claim_type} is covered (max ${chunk_max})"
                        }
                    else:
                        # No max found in chunk, but item is covered
                        return {
                            "decision": "REVIEW",
                            "reason": f"{claim.claim_type} covered but max amount not specified in policy"
                        }
        
        # Item not found in any chunk
        return {
            "decision": "REVIEW",
            "reason": "Unable to determine coverage - needs review"
        }
    
    # No chunks available
    return {
        "decision": "REVIEW",
        "reason": "No policy chunks retrieved - needs review"
    }

def human_review_node(state: AgentState) -> AgentState:
    """
     FIXED: Skip input() during automated testing
    """
    print("\n HUMAN REVIEW REQUIRED")
    print(f"Customer: {state['claim'].customer_name}")
    print(f"Claim Type: {state['claim'].claim_type}")
    print(f"Amount: ${state['claim'].amount}")
    
    #  During testing: Auto-flag as REVIEW (don't ask user)
    # When deployed: Actual human would review this
    return {
        "decision": "REVIEW",
        "reason": "Flagged for human review - awaiting decision"
    }

def final_result_node(state: AgentState) -> AgentState:
    print("\n" + "="*50)
    print("FINAL CLAIM RESULT")
    print(f"Customer: {state['claim'].customer_name}")
    print(f"Claim Type: {state['claim'].claim_type}")
    print(f"Amount: ${state['claim'].amount}")
    print(f"Decision: {state['decision']}")
    print(f"Reason: {state['reason']}")
    print("="*50)
    return state


