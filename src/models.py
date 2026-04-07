from pydantic import BaseModel, Field
from typing import List, Optional, TypedDict, Dict, Any
from datetime import datetime
from enum import Enum



# ENUMS - Define allowed values for status, decisions, etc.

class StatusEnum(str, Enum):
    """Claim lifecycle status"""
    INTAKE = "INTAKE"
    COVERAGE_CHECK = "COVERAGE_CHECK"
    DECISION = "DECISION"
    CLOSED = "CLOSED"


class DecisionEnum(str, Enum):
    """Possible claim decisions"""
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REVIEW = "REVIEW"


class HandledByEnum(str, Enum):
    """Who made the decision"""
    AI = "AI"
    HUMAN = "HUMAN"



# WARRANTY MODELS 

class WarrantyCoverage(BaseModel):
    item: str = Field(description="Item covered under warranty")
    duration_months: int = Field(description="Coverage duration in months")
    covered: bool = Field(description="Is item covered or not")
    max_amount: Optional[float] = Field(description="Maximum coverage amount", default=None)


class WarrantyPolicy(BaseModel):
    policy_name: str = Field(description="Name of the warranty policy")
    covered_items: List[WarrantyCoverage] = Field(description="List of covered items")
    excluded_items: List[str] = Field(description="List of excluded items")
    requires_receipt: bool = Field(description="Does customer need receipt")
    repair_days: int = Field(description="Maximum repair time in days")



# CLAIM MODELS 
class ClaimRequest(BaseModel):
    customer_name: str = Field(description="Name of the customer")
    claim_type: str = Field(description="Type of claim")
    amount: float = Field(description="Amount of claim requested")
    description: Optional[str] = Field(description="Claim description", default=None)


class ClaimResult(BaseModel):
    decision: str = Field(description="APPROVE, REJECT or REVIEW")
    reason: str = Field(description="Why claim was approved or rejected")
    amount_approved: float = Field(description="How much will be paid")
    handled_by: str = Field(description="Human or AI")



#  MODELS for tracking and auditing

class AuditLog(BaseModel):
    """Every action in the system gets logged here"""
    log_id: str = Field(description="Unique log identifier")
    claim_id: str = Field(description="Which claim is this log for")
    node_name: str = Field(description="Which node executed this (e.g., coverage_check_node)")
    action: str = Field(description="What action was taken (e.g., Retrieved policies)")
    status: str = Field(description="Did it succeed? SUCCESS or ERROR")
    input_data: Optional[Dict[str, Any]] = Field(description="Data that went into this node", default=None)
    output_data: Optional[Dict[str, Any]] = Field(description="Data that came out of this node", default=None)
    error_message: Optional[str] = Field(description="If it failed, what was the error?", default=None)
    duration_ms: Optional[float] = Field(description="How long did this take in milliseconds?", default=None)
    created_at: datetime = Field(description="When did this happen?", default_factory=datetime.utcnow)
    user_id: Optional[str] = Field(description="Who triggered this? (optional)", default=None)


class ClaimMetadata(BaseModel):
    """Track the lifecycle and metadata of a claim"""
    claim_id: str = Field(description="Unique claim identifier")
    created_at: datetime = Field(description="When was the claim submitted?")
    updated_at: Optional[datetime] = Field(description="When was it last changed?", default=None)
    status: str = Field(description="Current state (INTAKE, COVERAGE_CHECK, DECISION, CLOSED)")
    confidence_score: Optional[float] = Field(description="AI confidence in its decision (0-1)", default=None)
    handled_by: Optional[str] = Field(description="Was it decided by AI or HUMAN?", default=None)
    source: Optional[str] = Field(description="Where did this claim come from? (API, EMAIL, PHONE, WEB_FORM)", default=None)
    notes: Optional[str] = Field(description="Any special notes about this claim", default=None)


class EvaluationMetric(BaseModel):
    """Track system performance metrics"""
    metric_id: str = Field(description="Unique metric identifier")
    metric_name: str = Field(description="What are we measuring? (accuracy, precision, recall, f1_score, fraud_detection_rate)")
    metric_value: float = Field(description="The actual value (e.g., 0.92 for 92% accuracy)")
    expected_value: Optional[float] = Field(description="What was the target? (e.g., 0.95 for 95%)", default=None)
    test_type: Optional[str] = Field(description="Type of test (golden_set, regression, production)", default=None)
    description: Optional[str] = Field(description="Human-readable description", default=None)
    created_at: datetime = Field(description="When was this measured?", default_factory=datetime.utcnow)



# AGENT STATE - LangGraph workflow state 

class AgentState(TypedDict):
    """State dictionary for LangGraph workflow"""
    pdf_path: str
    policy: Optional[WarrantyPolicy]
    claim: Optional[ClaimRequest]
    result: Optional[ClaimResult]
    decision: str
    reason: str
    error: Optional[str]