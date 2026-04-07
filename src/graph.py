from langgraph.graph import StateGraph, END
from models import AgentState
from nodes import (
    ingest_node,
    receive_claim_node,
    check_coverage_node,
    human_review_node,
    final_result_node
)
from retrieval_node import retrieval_node

def route_decision(state: AgentState) -> str:
    decision = state["decision"]
    if decision == "APPROVE":
        return "approve"
    elif decision == "REJECT":
        return "reject"
    else:
        return "human" 

def build_graph():
    graph = StateGraph(AgentState)

    # Add nodes
    graph.add_node("ingest_node", ingest_node)
    graph.add_node("receive_claim_node", receive_claim_node)
    graph.add_node("retrieval_node", retrieval_node)
    graph.add_node("check_coverage_node", check_coverage_node)
    graph.add_node("human_review_node", human_review_node)
    graph.add_node("final_result_node", final_result_node)

    # Entry point
    graph.set_entry_point("ingest_node")

    # Edges
    graph.add_edge("ingest_node", "receive_claim_node")
    graph.add_edge("receive_claim_node", "retrieval_node")  
    graph.add_edge("retrieval_node", "check_coverage_node")

    # Conditional edges
    graph.add_conditional_edges(
        "check_coverage_node",
        route_decision,
        {
            "approve": "final_result_node",
            "reject":  "final_result_node",
            "human":   "human_review_node",
        }
    )

    graph.add_edge("human_review_node", "final_result_node")
    graph.add_edge("final_result_node", END)

    return graph.compile()

app = build_graph()