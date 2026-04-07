"""
API Usage Guide and Tests

Run the API:
  python api.py
  OR
  uvicorn api:app --reload

Then test with:
  python test_api.py
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

# ============================================================
# 📋 TEST CASES
# ============================================================

def test_health_check():
    """Test 1: Health check"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2, default=str))
    assert response.status_code == 200


def test_evaluate_claim_approved():
    """Test 2: Normal claim that should be APPROVED"""
    print("\n" + "="*60)
    print("TEST 2: Evaluate Claim - Should APPROVE")
    print("="*60)
    
    claim = {
        "customer_name": "John Doe",
        "customer_id": "CUST-001",
        "claim_type": "Battery",
        "amount": 300.0,
        "description": "Battery not holding charge after 3 months of use",
        "days_since_purchase": 90,
        "has_receipt": True,
        "policy_id": "POL-LAPTOP-001"
    }
    
    response = requests.post(f"{BASE_URL}/claims/evaluate", json=claim)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, default=str))
    
    assert response.status_code == 200
    assert data["decision"] == "APPROVE"
    return data["claim_id"]  # Return claim ID for next test


def test_evaluate_claim_review():
    """Test 3: Claim with fraud signals - should REVIEW"""
    print("\n" + "="*60)
    print("TEST 3: Evaluate Claim - Should REVIEW (Fraud Signals)")
    print("="*60)
    
    claim = {
        "customer_name": "Jane Smith",
        "customer_id": "CUST-002",
        "claim_type": "Motherboard",
        "amount": 900.0,
        "description": "Motherboard failed",
        "days_since_purchase": 2,  # Very early!
        "has_receipt": True,
        "policy_id": "POL-LAPTOP-001"
    }
    
    response = requests.post(f"{BASE_URL}/claims/evaluate", json=claim)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, default=str))
    
    assert response.status_code == 200
    assert data["decision"] == "REVIEW"  # Should trigger review due to early claim
    assert len(data["fraud_signals"]) > 0
    return data["claim_id"]


def test_evaluate_claim_rejected():
    """Test 4: Excluded item - should REJECT"""
    print("\n" + "="*60)
    print("TEST 4: Evaluate Claim - Should REJECT (Excluded)")
    print("="*60)
    
    claim = {
        "customer_name": "Bob Wilson",
        "customer_id": "CUST-003",
        "claim_type": "Screen Damage",
        "amount": 600.0,
        "description": "Screen is cracked",
        "days_since_purchase": 100,
        "has_receipt": True,
        "policy_id": "POL-LAPTOP-001"
    }
    
    response = requests.post(f"{BASE_URL}/claims/evaluate", json=claim)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, default=str))
    
    assert response.status_code == 200
    assert data["decision"] == "REJECT"
    return data["claim_id"]


def test_get_claim_details(claim_id):
    """Test 5: Get claim details"""
    print("\n" + "="*60)
    print(f"TEST 5: Get Claim Details - {claim_id}")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/claims/{claim_id}")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, default=str))
    
    assert response.status_code == 200
    assert data["claim_id"] == claim_id


def test_get_metrics():
    """Test 6: Get system metrics"""
    print("\n" + "="*60)
    print("TEST 6: Get System Metrics")
    print("="*60)
    
    response = requests.get(f"{BASE_URL}/metrics")
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, default=str))
    
    assert response.status_code == 200
    assert data["total_claims"] > 0


def test_submit_feedback(claim_id):
    """Test 7: Submit feedback"""
    print("\n" + "="*60)
    print(f"TEST 7: Submit Feedback - {claim_id}")
    print("="*60)
    
    feedback = {
        "claim_id": claim_id,
        "actual_decision": "APPROVE",
        "feedback_type": "correct",
        "notes": "Our decision was correct"
    }
    
    response = requests.post(f"{BASE_URL}/claims/{claim_id}/feedback", json=feedback)
    print(f"Status: {response.status_code}")
    data = response.json()
    print(json.dumps(data, indent=2, default=str))
    
    assert response.status_code == 200


def test_error_handling():
    """Test 8: Error handling"""
    print("\n" + "="*60)
    print("TEST 8: Error Handling")
    print("="*60)
    
    # Invalid amount
    print("\n8a. Test invalid amount (negative):")
    claim = {
        "customer_name": "Test",
        "customer_id": "CUST-004",
        "claim_type": "Battery",
        "amount": -100.0,  # Invalid!
        "description": "This should fail because amount is negative",
        "days_since_purchase": 90,
        "has_receipt": True,
        "policy_id": "POL-LAPTOP-001"
    }
    
    response = requests.post(f"{BASE_URL}/claims/evaluate", json=claim)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 422  # Validation error
    
    # Non-existent claim
    print("\n8b. Test getting non-existent claim:")
    response = requests.get(f"{BASE_URL}/claims/CLM-NONEXISTENT")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 404


# ============================================================
# 🧪 RUN ALL TESTS
# ============================================================

def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("WARRANTY CLAIMS API - COMPLETE TEST SUITE")
    print("="*70)
    
    try:
        # Test 1
        test_health_check()
        
        # Test 2
        claim_id_1 = test_evaluate_claim_approved()
        
        # Test 3
        claim_id_2 = test_evaluate_claim_review()
        
        # Test 4
        claim_id_3 = test_evaluate_claim_rejected()
        
        # Test 5
        test_get_claim_details(claim_id_1)
        
        # Test 6
        test_get_metrics()
        
        # Test 7
        test_submit_feedback(claim_id_1)
        
        # Test 8
        test_error_handling()
        
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Waiting for API to start on http://localhost:8000...")
    import time
    time.sleep(2)
    run_all_tests()
