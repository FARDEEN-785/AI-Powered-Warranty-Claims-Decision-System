import json
from typing import Dict, List, Tuple
from graph import app
from models import ClaimRequest
from database import get_db
from embeddings import load_embedding_model, embed_text
from retrieval_node import vector_store
from chunking import chunk_warranty_text
from ingest import ingest_warranty
import time

db = get_db()


def populate_vector_store(policy_pdf_path: str = "data/Laptop_policy.pdf") -> None:
    """
     NEW: Populate vector store with policy chunks from PDF.
    
    This MUST be done before running evaluation!
    """
    print("Populating vector store with policy chunks...")
    
    try:
        # Step 1: Extract policy from PDF
        policy = ingest_warranty(policy_pdf_path)
        
        # Step 2: Create policy text
        policy_text = f"{policy.policy_name}\n\n"
        
        # Add covered items
        policy_text += "Covered Items:\n"
        for item in policy.covered_items:
            policy_text += f"- {item.item}: Covered for {item.duration_months} months. Max coverage: ${item.max_amount if item.max_amount else 'Unlimited'}\n"
        
        # Add excluded items
        policy_text += "\nExcluded Items:\n"
        for excluded in policy.excluded_items:
            policy_text += f"- {excluded}: NOT covered\n"
        
        # Step 3: Chunk the policy text
        chunks = chunk_warranty_text(policy_text, chunk_size=200, overlap=50)
        print(f"  Created {len(chunks)} chunks from policy")
        
        # Step 4: Embed chunks
        model = load_embedding_model()
        embeddings = [embed_text(model, chunk) for chunk in chunks]
        
        # Step 5: Add to vector store
        vector_store.add_chunks(chunks, embeddings)
        print(f" Vector store populated with {len(chunks)} policy chunks\n")
        
    except Exception as e:
        print(f" Error populating vector store: {e}")
        import traceback
        traceback.print_exc()


def load_golden_test_set(filepath: str = "E:/LLM_RAG/Agentic_AI/Warranty_Agent_Project/golden_test_set.json") -> dict:
    """
    Load golden test set from JSON file.
    
    Args:
        filepath: Path to golden_test_set.json
    
    Returns:
        Dictionary with test cases
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        print(f" Loaded golden test set: {filepath}")
        return data
    except FileNotFoundError:
        print(f" Error: {filepath} not found")
        return {}
    except json.JSONDecodeError:
        print(f" Error: {filepath} is not valid JSON")
        return {}


def run_test_case(test_case: dict) -> Tuple[str, str]:
    """
    Run a single test case through the graph.
    
    Args:
        test_case: A single test case from golden_test_set
    
    Returns:
        Tuple of (actual_decision, actual_reason)
    """
    try:
        # Extract claim data directly from test_case
        claim = ClaimRequest(
            customer_name=test_case['customer_name'],
            claim_type=test_case['claim_type'],
            amount=test_case['amount'],
            description=test_case.get('description', '')
        )
        
        # Create state
        state = {
            "pdf_path": "data/Laptop_policy.pdf",
            "policy": None,
            "claim": claim,
            "result": None,
            "decision": None,
            "reason": None,
            "error": None,
            "days_since_purchase": test_case.get('days_since_purchase', 0),
            "has_receipt": test_case.get('has_receipt', True),
            "max_amount": 500.0  # Default max
        }
        
        # Run graph (suppress output)
        result = app.invoke(state)
        
        # Return decision and reason
        return result.get('decision', 'UNKNOWN'), result.get('reason', 'Unknown reason')
    
    except Exception as e:
        return "ERROR", str(e)


def compare_results(expected: str, actual: str) -> bool:
    """
    Compare expected vs actual decision.
    
    Args:
        expected: Expected decision (APPROVE, REJECT, REVIEW)
        actual: Actual decision from graph
    
    Returns:
        True if match, False if mismatch
    """
    return expected.upper() == actual.upper()


def calculate_metrics(results: List[dict]) -> dict:
    """
    Calculate evaluation metrics from results.
    
    Args:
        results: List of test results
    
    Returns:
        Dictionary with metrics
    """
    if not results:
        return {}
    
    # Count overall metrics
    total = len(results)
    passed = sum(1 for r in results if r['match'])
    failed = total - passed
    accuracy = (passed / total * 100) if total > 0 else 0
    
    # Group by category
    by_category = {}
    for result in results:
        category = result.get('category', 'Unknown')
        if category not in by_category:
            by_category[category] = {'total': 0, 'passed': 0, 'tests': []}
        
        by_category[category]['total'] += 1
        if result['match']:
            by_category[category]['passed'] += 1
        else:
            by_category[category]['tests'].append(result)
    
    # Calculate category accuracy
    category_metrics = {}
    for category, data in by_category.items():
        cat_accuracy = (data['passed'] / data['total'] * 100) if data['total'] > 0 else 0
        category_metrics[category] = {
            'total': data['total'],
            'passed': data['passed'],
            'failed': data['total'] - data['passed'],
            'accuracy': round(cat_accuracy, 2)
        }
    
    # Get failed tests
    failed_tests = [r for r in results if not r['match']]
    
    return {
        'total_tests': total,
        'passed': passed,
        'failed': failed,
        'accuracy': round(accuracy, 2),
        'by_category': category_metrics,
        'failed_tests': failed_tests
    }


def run_evaluation(golden_set_path: str = "golden_test_set.json") -> dict:
    """
    Run complete evaluation on golden test set.
    
    Args:
        golden_set_path: Path to golden_test_set.json
    
    Returns:
        Dictionary with evaluation results
    """
    #  NEW: Populate vector store first!
    populate_vector_store("data/Laptop_policy.pdf")
    
    # Load golden test set
    print("Loading golden test set...")
    golden_set = load_golden_test_set(golden_set_path)
    
    if not golden_set or 'test_cases' not in golden_set:
        print(" Failed to load golden test set")
        return {}
    
    # Extract all test cases
    all_tests = []
    for category, tests in golden_set['test_cases'].items():
        for test_id, test_case in tests.items():
            test_case['test_id'] = test_id
            test_case['category'] = category
            all_tests.append(test_case)
    
    print(f" Loaded {len(all_tests)} test cases\n")
    
    # Run tests
    print("Starting evaluation... (this may take a few minutes)")
    results = []
    start_time = time.time()
    
    for i, test_case in enumerate(all_tests, 1):
        test_id = test_case['test_id']
        expected_decision = test_case['expected_decision']
        category = test_case['category']
        
        print(f"  Running test {i}/{len(all_tests)}: {test_id} ({category})...", end=" ")
        
        # Run test
        actual_decision, actual_reason = run_test_case(test_case)
        
        # Compare
        match = compare_results(expected_decision, actual_decision)
        
        # Store result
        result = {
            'test_id': test_id,
            'category': category,
            'expected_decision': expected_decision,
            'actual_decision': actual_decision,
            'expected_reason': test_case['expected_reason'],
            'actual_reason': actual_reason,
            'match': match
        }
        results.append(result)
        
        # Print result
        status = " PASS" if match else " FAIL"
        print(status)
    
    end_time = time.time()
    elapsed_time = round(end_time - start_time, 2)
    
    print(f"\n Evaluation completed in {elapsed_time} seconds\n")
    
    # Calculate metrics
    metrics = calculate_metrics(results)
    metrics['elapsed_time'] = elapsed_time
    
    return metrics


def print_evaluation_summary(metrics: dict) -> None:
    """
    Print evaluation results in nice format.
    
    Args:
        metrics: Results from calculate_metrics()
    """
    if not metrics:
        print(" No metrics to display")
        return
    
    print("=" * 70)
    print("EVALUATION RESULTS SUMMARY")
    print("=" * 70)
    
    print(f"\nOverall Performance:")
    print(f"  Total Tests: {metrics['total_tests']}")
    print(f"  Passed: {metrics['passed']} ")
    print(f"  Failed: {metrics['failed']} ")
    print(f"  Accuracy: {metrics['accuracy']}%")
    print(f"  Time: {metrics.get('elapsed_time', 'N/A')} seconds")
    
    print(f"\nResults by Category:")
    for category, cat_metrics in metrics['by_category'].items():
        accuracy = cat_metrics['accuracy']
        passed = cat_metrics['passed']
        total = cat_metrics['total']
        status = "Accepted" if accuracy == 100 else "Review" if accuracy >= 80 else "Rejected"
        print(f"  {status} {category}")
        print(f"     {passed}/{total} passed ({accuracy}%)")
    
    # Show failed tests
    if metrics['failed_tests']:
        print(f"\nFailed Tests ({len(metrics['failed_tests'])}):")
        for failed in metrics['failed_tests'][:10]:  # Show first 10
            print(f"   {failed['test_id']}")
            print(f"     Expected: {failed['expected_decision']}")
            print(f"     Got: {failed['actual_decision']}")
        
        if len(metrics['failed_tests']) > 10:
            print(f"  ... and {len(metrics['failed_tests']) - 10} more")
    
    print("\n" + "=" * 70)


def save_evaluation_results(metrics: dict, filepath: str = "evaluation_results.json") -> None:
    """
    Save evaluation results to JSON file.
    
    Args:
        metrics: Results from calculate_metrics()
        filepath: Where to save results
    """
    try:
        with open(filepath, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f" Results saved to: {filepath}")
    except Exception as e:
        print(f" Error saving results: {e}")


# MAIN EXECUTION
if __name__ == "__main__":
    print("\n" + "="*70)
    print("GOLDEN TEST SET EVALUATION")
    print("="*70 + "\n")
    
    # Run evaluation
    results = run_evaluation("golden_test_set.json")
    
    # Print summary
    print_evaluation_summary(results)
    
    # Save results
    save_evaluation_results(results, "evaluation_results.json")
    
    print("\n Evaluation complete!")
    print(f" Full results saved to: evaluation_results.json")