"""
Fraud Detection Module for Warranty Claims

Detects fraud patterns and risk signals:
- Multiple claims from same customer
- Claims too soon after purchase
- Excessive claim amounts
- Unusual patterns (velocity, amount trends)
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

# Mock ClaimRequest for testing
@dataclass
class ClaimRequest:
    customer_name: str
    claim_type: str
    amount: float
    description: str


@dataclass
class FraudSignal:
    """Represents a single fraud risk signal"""
    signal_type: str  # "early_claim", "excessive_amount", "multiple_claims", etc.
    score: float  # 0-1
    reason: str
    severity: str  # "LOW", "MEDIUM", "HIGH"


@dataclass
class FraudAssessment:
    """Complete fraud assessment for a claim"""
    overall_risk_score: float  # 0-1
    signals: List[FraudSignal]
    requires_review: bool
    recommendation: str  # "APPROVE", "REVIEW", "REJECT"


class FraudDetector:
    """
    Fraud detection system for warranty claims.
    
    Risk Factors:
    1. Early Claims (within 2-7 days of purchase)
    2. Excessive Amounts (far above typical coverage)
    3. Multiple Claims (5+ claims from same customer in 6 months)
    4. Claim Velocity (claims coming too frequently)
    5. Amount Patterns (steadily increasing claim amounts)
    6. Device Age Mismatch (claiming defects on brand new device)
    """
    
    def __init__(self):
        """Initialize fraud detector with thresholds"""
        # Risk thresholds
        self.EARLY_CLAIM_DAYS = 7  # Claims within 7 days are suspicious
        self.EXCESSIVE_AMOUNT_MULTIPLIER = 2.0  # 2x typical coverage
        self.MULTIPLE_CLAIMS_THRESHOLD = 5  # 5+ claims in 6 months
        self.HIGH_VELOCITY_DAYS = 30  # Claims within 30 days are suspicious
        self.AMOUNT_SPIKE_THRESHOLD = 1.5  # 50% increase is suspicious
        
        # Typical coverage amounts by item type
        self.TYPICAL_COVERAGE = {
            "battery": 500,
            "motherboard": 800,
            "ram": 400,
            "keyboard": 250,
            "charging port": 250,
            "screen": 0,  # Not covered
            "water damage": 0,  # Not covered
        }
    
    def detect_early_claim_signal(self, days_since_purchase: int) -> Tuple[FraudSignal, None]:
        """
        Detect if claim is too soon after purchase.
        
        Logic:
        - 0-2 days: HIGH risk (someone bought device and claimed immediately)
        - 2-7 days: MEDIUM risk (suspicious timing)
        - 7+ days: LOW risk (normal)
        
        Why: Real defects take time to manifest. Claims on day 1 are often fraud.
        """
        if days_since_purchase <= 2:
            return FraudSignal(
                signal_type="early_claim",
                score=0.8,  # 80% risk
                reason=f"Claim made {days_since_purchase} days after purchase (immediate purchase + claim)",
                severity="HIGH"
            )
        elif days_since_purchase <= 7:
            return FraudSignal(
                signal_type="early_claim",
                score=0.5,  # 50% risk
                reason=f"Claim made {days_since_purchase} days after purchase (within 1 week)",
                severity="MEDIUM"
            )
        else:
            return None
    
    def detect_excessive_amount_signal(self, claim_amount: float, claim_type: str) -> FraudSignal or None:
        """
        Detect if claim amount is excessively high.
        
        Logic:
        - Get typical coverage for claim type
        - If actual > typical * 2.0 → HIGH risk
        - If actual > typical * 1.5 → MEDIUM risk
        - Otherwise → OK
        
        Why: Insurance fraud often involves inflated amounts.
        """
        claim_type_lower = claim_type.lower()
        typical_amount = self.TYPICAL_COVERAGE.get(claim_type_lower, 500)
        
        # Skip if not covered at all
        if typical_amount == 0:
            return None
        
        # Check if amount is excessive
        if claim_amount > typical_amount * 2.0:
            return FraudSignal(
                signal_type="excessive_amount",
                score=0.7,  # 70% risk
                reason=f"Claim amount ${claim_amount} is 2x typical coverage (${typical_amount})",
                severity="HIGH"
            )
        elif claim_amount > typical_amount * 1.5:
            return FraudSignal(
                signal_type="excessive_amount",
                score=0.4,  # 40% risk
                reason=f"Claim amount ${claim_amount} is 1.5x typical coverage (${typical_amount})",
                severity="MEDIUM"
            )
        
        return None
    
    def detect_multiple_claims_signal(  self,  customer_id: str, claim_history: List[Dict],  days_lookback: int = 180  ) -> FraudSignal or None:
        """
        Detect if customer has too many claims.
        
        Logic:
        - Count claims in last 6 months
        - 5+ claims: HIGH risk (serial claimer)
        - 3-4 claims: MEDIUM risk (frequent)
        - < 3 claims: OK
        
        """
        # Filter claims from last N days
        recent_claims = [
            c for c in claim_history
            if c.get('days_since_purchase', 0) < days_lookback
        ]
        
        claim_count = len(recent_claims)
        
        if claim_count >= self.MULTIPLE_CLAIMS_THRESHOLD:
            return FraudSignal(
                signal_type="multiple_claims",
                score=0.75,  # 75% risk
                reason=f"Customer has {claim_count} claims in last 6 months (threshold: {self.MULTIPLE_CLAIMS_THRESHOLD})",
                severity="HIGH"
            )
        elif claim_count >= 3:
            return FraudSignal(
                signal_type="multiple_claims",
                score=0.45,  # 45% risk
                reason=f"Customer has {claim_count} claims in last 6 months (frequent claimer)",
                severity="MEDIUM"
            )
        
        return None
    
    def detect_claim_velocity_signal( self, claim_history: List[Dict],days_lookback: int = 30 ) -> FraudSignal or None:
        """
        Detect if claims are coming too frequently.
        
        Logic:
        - Count claims in last 30 days
        - 2+ claims in 30 days: MEDIUM risk (high velocity)
        - 3+ claims in 30 days: HIGH risk (very high velocity)
        
        Why: Real defects don't happen multiple times per month on same device.
        """
        # Filter claims from last N days
        recent_claims = [
            c for c in claim_history
            if c.get('days_since_purchase', 0) < days_lookback
        ]
        
        claim_count = len(recent_claims)
        
        if claim_count >= 3:
            return FraudSignal(
                signal_type="high_claim_velocity",
                score=0.6,  # 60% risk
                reason=f"Customer filed {claim_count} claims in last {days_lookback} days",
                severity="HIGH"
            )
        elif claim_count >= 2:
            return FraudSignal(
                signal_type="high_claim_velocity",
                score=0.4,  # 40% risk
                reason=f"Customer filed {claim_count} claims in last {days_lookback} days",
                severity="MEDIUM"
            )
        
        return None
    
    def detect_amount_pattern_signal(self, current_amount: float, claim_history: List[Dict]  ) -> FraudSignal or None:
        """
        Detect unusual amount patterns (escalating amounts).
        
        Logic:
        - If previous claim was lower, and this one is 50%+ higher: suspicious
        - Compare to customer's  claim amount
        
        """
        if not claim_history or len(claim_history) < 2:
            return None
        
        # Get previous claim amount
        previous_claim = claim_history[-1]
        previous_amount = previous_claim.get('amount', 0)
        
        if previous_amount == 0:
            return None
        
        # Check for spike
        percentage_increase = (current_amount - previous_amount) / previous_amount
        
        if percentage_increase >= self.AMOUNT_SPIKE_THRESHOLD:
            return FraudSignal(
                signal_type="amount_escalation",
                score=0.5,  # 50% risk
                reason=f"Claim amount increased {percentage_increase*100:.0f}% from previous claim (${previous_amount} → ${current_amount})",
                severity="MEDIUM"
            )
        
        return None
    
    def assess_fraud_risk(self,  claim: ClaimRequest, customer_id: str, claim_history: List[Dict], days_since_purchase: int ) -> FraudAssessment:
        """
        Comprehensive fraud assessment for a claim.
        
        Args:
            claim: The current claim
            customer_id: Customer making the claim
            claim_history: Previous claims from this customer
            days_since_purchase: Days elapsed since device purchase
        
        Returns:
            FraudAssessment with risk score and signals
        """
        signals: List[FraudSignal] = []
        
        # Check all fraud signals
        early_claim = self.detect_early_claim_signal(days_since_purchase)
        if early_claim:
            signals.append(early_claim)
        
        excessive_amount = self.detect_excessive_amount_signal(claim.amount, claim.claim_type)
        if excessive_amount:
            signals.append(excessive_amount)
        
        multiple_claims = self.detect_multiple_claims_signal(customer_id, claim_history)
        if multiple_claims:
            signals.append(multiple_claims)
        
        velocity = self.detect_claim_velocity_signal(claim_history)
        if velocity:
            signals.append(velocity)
        
        amount_pattern = self.detect_amount_pattern_signal(claim.amount, claim_history)
        if amount_pattern:
            signals.append(amount_pattern)
        
        # Calculate overall risk score (0-1)
        if not signals:
            overall_score = 0.0
        else:
            # Average of all signal scores, weighted by severity
            total_score = 0.0
            weights = {"LOW": 1.0, "MEDIUM": 1.5, "HIGH": 2.0}
            total_weight = 0.0
            
            for signal in signals:
                weight = weights.get(signal.severity, 1.0)
                total_score += signal.score * weight
                total_weight += weight
            
            overall_score = total_score / total_weight if total_weight > 0 else 0.0
            overall_score = min(overall_score, 1.0)  # Cap at 1.0
        
        # Determine recommendation
        if overall_score >= 0.7:
            recommendation = "REJECT"
            requires_review = True
        elif overall_score >= 0.4:
            recommendation = "REVIEW"
            requires_review = True
        else:
            recommendation = "APPROVE"
            requires_review = False
        
        return FraudAssessment(
            overall_risk_score=round(overall_score, 2),
            signals=signals,
            requires_review=requires_review,
            recommendation=recommendation
        )
    


if __name__ == "__main__":
    detector = FraudDetector()
    
    # Test case 1: Normal claim
    claim1 = ClaimRequest(
        customer_name="John Doe",
        claim_type="Battery",
        amount=300.0,
        description="Battery not holding charge"
    )
    assessment1 = detector.assess_fraud_risk(
        claim=claim1,
        customer_id="CUST-001",
        claim_history=[],
        days_since_purchase=90
    )
    
    # Simple print (no formatting)
    print(f"Test 1: Risk Score = {assessment1.overall_risk_score}")
    print(f"Recommendation = {assessment1.recommendation}")
    
    # Test case 2
    claim2 = ClaimRequest(
        customer_name="Jane Fraud",
        claim_type="Motherboard",
        amount=1000.0,
        description="Motherboard defective"
    )
    claim_history2 = [
        {"amount": 500, "days_since_purchase": 5},
        {"amount": 600, "days_since_purchase": 15},
        {"amount": 700, "days_since_purchase": 25},
    ]
    assessment2 = detector.assess_fraud_risk(
        claim=claim2,
        customer_id="CUST-002",
        claim_history=claim_history2,
        days_since_purchase=2
    )
    print(f"Test 2: Risk Score = {assessment2.overall_risk_score}")
    print(f"Recommendation = {assessment2.recommendation}")