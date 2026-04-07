"""
Tool Use / Function Calling for Warranty Claims Agent

Tools available:
- get_policy_coverage: Look up coverage for a claim type
- request_evidence: Request additional evidence from customer
- route_to_vendor: Route claim to repair/replacement vendor
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class PolicyCoverageRequest(BaseModel):
    """Request for policy coverage lookup"""
    claim_type: str = Field(..., description="Type of claim (Battery, Motherboard, etc.)")


class PolicyCoverageResponse(BaseModel):
    """Response with coverage information"""
    claim_type: str
    covered: bool
    months_covered: int = 0
    max_coverage: float = 0.0
    reason: str


class EvidenceRequest(BaseModel):
    """Request for additional evidence"""
    claim_id: str = Field(..., description="The claim ID")
    evidence_type: str = Field(..., description="Type of evidence needed (photo, receipt, diagnostic)")


class EvidenceResponse(BaseModel):
    """Response confirming evidence request"""
    claim_id: str
    evidence_requested: str
    status: str
    message: str


class VendorRoutingRequest(BaseModel):
    """Request to route claim to vendor"""
    claim_id: str = Field(..., description="The claim ID")
    repair_type: str = Field(..., description="Type of repair (battery_replacement, motherboard_repair, full_replacement)")


class VendorRoutingResponse(BaseModel):
    """Response confirming vendor routing"""
    claim_id: str
    vendor_assigned: str
    repair_type: str
    status: str
    vendor_contact: str



# TOOL IMPLEMENTATIONS


class PolicyLookupTool:
    """Tool to look up coverage from warranty policy"""
    
    # Coverage database (from your warranty policy)
    COVERAGE_DATABASE = {
        "battery": {
            "covered": True,
            "months": 12,
            "max_coverage": 500.0,
            "reason": "Battery degradation covered for 12 months"
        },
        "motherboard": {
            "covered": True,
            "months": 24,
            "max_coverage": 800.0,
            "reason": "Manufacturing defects covered for 24 months"
        },
        "ram": {
            "covered": True,
            "months": 24,
            "max_coverage": 400.0,
            "reason": "Memory defects fully covered for 24 months"
        },
        "keyboard": {
            "covered": True,
            "months": 12,
            "max_coverage": 250.0,
            "reason": "Mechanical failures covered for 12 months"
        },
        "charging port": {
            "covered": True,
            "months": 12,
            "max_coverage": 250.0,
            "reason": "Port defects covered for 12 months"
        },
        "screen": {
            "covered": False,
            "months": 0,
            "max_coverage": 0.0,
            "reason": "Screen damage is NOT covered under warranty"
        },
        "water damage": {
            "covered": False,
            "months": 0,
            "max_coverage": 0.0,
            "reason": "Water damage is NOT covered under any circumstances"
        },
        "physical damage": {
            "covered": False,
            "months": 0,
            "max_coverage": 0.0,
            "reason": "Physical damage from impacts is NOT covered"
        }
    }
    
    @staticmethod
    def execute(claim_type: str) -> PolicyCoverageResponse:
        """
        Look up coverage for a claim type in the policy.
        
        Args:
            claim_type: Type of claim (Battery, Screen, etc.)
        
        Returns:
            PolicyCoverageResponse with coverage details
        """
        claim_type_lower = claim_type.lower()
        
        # Look up coverage
        coverage_info = PolicyLookupTool.COVERAGE_DATABASE.get(
            claim_type_lower,
            {
                "covered": False,
                "months": 0,
                "max_coverage": 0.0,
                "reason": f"No coverage information found for {claim_type}"
            }
        )
        
        return PolicyCoverageResponse(
            claim_type=claim_type,
            covered=coverage_info["covered"],
            months_covered=coverage_info["months"],
            max_coverage=coverage_info["max_coverage"],
            reason=coverage_info["reason"]
        )


class EvidenceTool:
    """Tool to request additional evidence from customer"""
    
    # Track evidence requests (in production: database)
    evidence_requests_db = {}
    
    @staticmethod
    def execute(claim_id: str, evidence_type: str) -> EvidenceResponse:
        """
        Request additional evidence from customer.
        
        Args:
            claim_id: The claim ID
            evidence_type: Type of evidence (photo, receipt, diagnostic)
        
        Returns:
            EvidenceResponse confirming request
        """
        valid_evidence_types = ["photo", "receipt", "diagnostic", "invoice", "proof_of_purchase"]
        
        if evidence_type not in valid_evidence_types:
            return EvidenceResponse(
                claim_id=claim_id,
                evidence_requested=evidence_type,
                status="FAILED",
                message=f"Invalid evidence type. Valid types: {', '.join(valid_evidence_types)}"
            )
        
        # Record evidence request
        EvidenceTool.evidence_requests_db[claim_id] = {
            "type": evidence_type,
            "status": "REQUESTED",
            "timestamp": "2024-03-19T10:30:00Z"
        }
        
        return EvidenceResponse(
            claim_id=claim_id,
            evidence_requested=evidence_type,
            status="REQUESTED",
            message=f"Evidence request sent to customer. They have 7 days to respond."
        )


class VendorRoutingTool:
    """Tool to route claim to vendor for repair/replacement"""
    
    # Vendor database (in production: external vendor system)
    VENDORS = {
        "battery_replacement": {
            "vendor": "TechRepair Co",
            "contact": "support@techrepair.com",
            "phone": "1-800-REPAIR-1",
            "turnaround": "3-5 business days"
        },
        "motherboard_repair": {
            "vendor": "CircuitFix Inc",
            "contact": "claims@circuitfix.com",
            "phone": "1-800-CIRCUIT-1",
            "turnaround": "5-7 business days"
        },
        "full_replacement": {
            "vendor": "Warranty Fulfillment Center",
            "contact": "fulfillment@warrantyfc.com",
            "phone": "1-800-WARRAN-1",
            "turnaround": "7-10 business days"
        }
    }
    
    @staticmethod
    def execute(claim_id: str, repair_type: str) -> VendorRoutingResponse:
        """
        Route claim to appropriate vendor.
        
        Args:
            claim_id: The claim ID
            repair_type: Type of repair (battery_replacement, motherboard_repair, full_replacement)
        
        Returns:
            VendorRoutingResponse with vendor details
        """
        vendor_info = VendorRoutingTool.VENDORS.get(
            repair_type,
            None
        )
        
        if not vendor_info:
            return VendorRoutingResponse(
                claim_id=claim_id,
                vendor_assigned="UNKNOWN",
                repair_type=repair_type,
                status="FAILED",
                vendor_contact="Unable to route - invalid repair type"
            )
        
        return VendorRoutingResponse(
            claim_id=claim_id,
            vendor_assigned=vendor_info["vendor"],
            repair_type=repair_type,
            status="ROUTED",
            vendor_contact=f"{vendor_info['contact']} | {vendor_info['phone']}"
        )


# TOOL REGISTRY 

TOOLS = {
    "get_policy_coverage": {
        "function": PolicyLookupTool.execute,
        "description": "Look up warranty coverage for a claim type from the policy",
        "parameters": {
            "claim_type": "Type of claim (Battery, Motherboard, RAM, Keyboard, Charging Port, Screen, etc.)"
        }
    },
    "request_evidence": {
        "function": EvidenceTool.execute,
        "description": "Request additional evidence from customer for claim verification",
        "parameters": {
            "claim_id": "The claim ID",
            "evidence_type": "Type of evidence (photo, receipt, diagnostic, invoice, proof_of_purchase)"
        }
    },
    "route_to_vendor": {
        "function": VendorRoutingTool.execute,
        "description": "Route claim to vendor for repair or replacement",
        "parameters": {
            "claim_id": "The claim ID",
            "repair_type": "Type of repair (battery_replacement, motherboard_repair, full_replacement)"
        }
    }
}



# EXAMPLE 

if __name__ == "__main__":
    print("=" * 70)
    print("WARRANTY CLAIMS AGENT - TOOL DEMONSTRATIONS")
    print("=" * 70)
    
    # Tool 1: Policy Coverage Lookup
    print("\n1. GET_POLICY_COVERAGE Tool")
    print("-" * 70)
    
    for claim_type in ["Battery", "Screen", "Motherboard"]:
        result = PolicyLookupTool.execute(claim_type)
        print(f"\nClaim Type: {result.claim_type}")
        print(f"  Covered: {result.covered}")
        print(f"  Duration: {result.months_covered} months")
        print(f"  Max Coverage: ${result.max_coverage}")
        print(f"  Reason: {result.reason}")
    
    # Tool 2: Request Evidence
    print("\n\n2. REQUEST_EVIDENCE Tool")
    print("-" * 70)
    
    result = EvidenceTool.execute("CLM-001", "diagnostic")
    print(f"\nClaim ID: {result.claim_id}")
    print(f"Evidence Requested: {result.evidence_requested}")
    print(f"Status: {result.status}")
    print(f"Message: {result.message}")
    
    # Tool 3: Vendor Routing
    print("\n\n3. ROUTE_TO_VENDOR Tool")
    print("-" * 70)
    
    result = VendorRoutingTool.execute("CLM-001", "battery_replacement")
    print(f"\nClaim ID: {result.claim_id}")
    print(f"Vendor: {result.vendor_assigned}")
    print(f"Repair Type: {result.repair_type}")
    print(f"Status: {result.status}")
    print(f"Contact: {result.vendor_contact}")
    
    print("\n" + "=" * 70)
    print(" All tools working correctly!")
    print("=" * 70)