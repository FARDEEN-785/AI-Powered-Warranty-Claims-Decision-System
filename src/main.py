import os
from graph import app
from models import ClaimRequest

#  LangSmith setup
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = "YOUR_API_KEY"
os.environ["LANGCHAIN_PROJECT"] = "Warranty_Agent"  

print("="*50)
print("WARRANTY CLAIMS AGENT")
print("="*50)

#  Get user input
pdf_path = input("\nEnter PDF path: ")
customer_name = input("Enter your name: ")
claim_type = input("Enter claim type: ")
amount = float(input("Enter claim amount: $"))

#  Create ClaimRequest
claim = ClaimRequest(
    customer_name=customer_name,
    claim_type=claim_type,
    amount=amount
)

#  Build initial state
initial_state = {
    "pdf_path": pdf_path,
    "claim": claim,
    "policy": None,
    "decision": "",
    "reason": ""
}

print("\nProcessing claim...")

#  Run graph
result = app.invoke(initial_state)

print("\n Done! Check LangSmith for full trace!")