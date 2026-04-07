"""
DATABASE.PY - Complete SQLite Database Layer for SureBright
Handles all database operations: create tables, save/retrieve claims, audit logging
"""

import sqlite3
import json
import uuid
from datetime import datetime
from pathlib import Path


class SureBrightDB:
    """SQLite database for warranty claims and audit trails"""
    
    def __init__(self, db_path: str = "surebright.db"):
        """
        Initialize database connection and create tables if needed.
        
        Args:
            db_path: Path to SQLite database file (default: "surebright.db")
        """
        self.db_path = db_path
        db_exists = Path(db_path).exists()
        
        if not db_exists:
            print(f"📁 Creating database: {db_path}")
            self.create_tables()
            print(f"✅ Database created successfully")
        else:
            print(f"✅ Using existing database: {db_path}")


    def create_tables(self):
        """Create all necessary tables in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # TABLE 1: CLAIMS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS claims (
                claim_id TEXT PRIMARY KEY,
                customer_name TEXT NOT NULL,
                claim_type TEXT NOT NULL,
                amount_requested REAL NOT NULL,
                amount_approved REAL DEFAULT 0,
                description TEXT, 
                decision TEXT,
                status TEXT,
                confidence_score REAL,
                handled_by TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # TABLE 2: AUDIT_LOGS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id TEXT PRIMARY KEY,
                claim_id TEXT NOT NULL,
                node_name TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                input_data_json TEXT,
                output_data_json TEXT,
                error_message TEXT,
                duration_ms REAL,
                created_at TIMESTAMP,
                user_id TEXT,
                FOREIGN KEY (claim_id) REFERENCES claims(claim_id)
            )
        """)
        
        # TABLE 3: POLICIES
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                policy_id TEXT PRIMARY KEY,
                policy_name TEXT NOT NULL,
                covered_items_json TEXT,
                excluded_items_json TEXT,
                requires_receipt BOOLEAN,
                repair_days INTEGER,
                created_at TIMESTAMP
            )
        """)
        
        # TABLE 4: EVALUATION_METRICS
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluation_metrics (
                metric_id TEXT PRIMARY KEY,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                expected_value REAL,
                test_type TEXT,
                description TEXT,
                created_at TIMESTAMP
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_created ON claims(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_claim_status ON claims(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_claim ON audit_logs(claim_id)")
        
        conn.commit()
        conn.close()
        print("  ✅ All tables created")


    # ========================================================================
    # CLAIM OPERATIONS
    # ========================================================================

    def save_claim(self, customer_name: str, claim_type: str, amount: float, description: str = None) -> str:
        """
        Save a new claim to database.
        
        Args:
            customer_name: Name of the customer
            claim_type: Type of claim (e.g., "Screen Damage")
            amount: Amount requested
            description: Optional description
            
        Returns:
            claim_id: The generated claim ID (e.g., "CLAIM-A1B2C3D4")
        """
        # Generate unique claim ID
        claim_id = f"CLAIM-{uuid.uuid4().hex[:8].upper()}"
        
        # Get current timestamp
        timestamp = datetime.utcnow()
        
        # Connect and insert
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO claims (claim_id, customer_name, claim_type, amount_requested, description, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (claim_id, customer_name, claim_type, amount, description, "INTAKE", timestamp, timestamp))
        
        conn.commit()
        conn.close()
        
        return claim_id


    def update_claim(self, claim_id: str, decision: str, amount_approved: float, reason: str) -> None:
        """
        Update claim with final decision.
        
        Args:
            claim_id: The claim to update
            decision: APPROVE, REJECT, or REVIEW
            amount_approved: Amount to pay
            reason: Explanation
        """
        timestamp = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE claims 
            SET decision = ?, amount_approved = ?, status = ?, updated_at = ?
            WHERE claim_id = ?
        """, (decision, amount_approved, "DECISION", timestamp, claim_id))
        
        conn.commit()
        conn.close()


    def get_claim(self, claim_id: str) -> dict:
        """
        Retrieve a claim by ID.
        
        Args:
            claim_id: The claim to retrieve
            
        Returns:
            Dictionary with claim data, or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM claims WHERE claim_id = ?", (claim_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None


    def get_claims_history(self, customer_name: str = None, limit: int = 100) -> list:
        """
        Get claim history with optional filtering.
        
        Args:
            customer_name: Optional filter by customer name
            limit: Max number of results
            
        Returns:
            List of claims as dictionaries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM claims WHERE 1=1"
        params = []
        
        if customer_name:
            query += " AND customer_name LIKE ?"
            params.append(f"%{customer_name}%")
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


    # ========================================================================
    # AUDIT LOG OPERATIONS
    # ========================================================================

    def log_action(self, claim_id: str, node_name: str, action: str, status: str,
                   input_data: dict = None, output_data: dict = None,
                   error_message: str = None, duration_ms: float = None, user_id: str = None) -> str:
        """
        Log an action to audit trail.
        
        Args:
            claim_id: Which claim
            node_name: Which node (e.g., "coverage_check_node")
            action: What happened
            status: SUCCESS or ERROR
            input_data: Optional input data
            output_data: Optional output data
            error_message: If failed, the error
            duration_ms: How long it took
            user_id: Who triggered it
            
        Returns:
            log_id: The generated log ID
        """
        # Generate log ID
        log_id = str(uuid.uuid4())
        timestamp = datetime.utcnow()
        
        # Convert dicts to JSON
        input_json = json.dumps(input_data) if input_data else None
        output_json = json.dumps(output_data) if output_data else None
        
        # Connect and insert
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO audit_logs (log_id, claim_id, node_name, action, status, input_data_json, output_data_json, error_message, duration_ms, created_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (log_id, claim_id, node_name, action, status, input_json, output_json, error_message, duration_ms, timestamp, user_id))
        
        conn.commit()
        conn.close()
        
        return log_id


    def get_audit_trail(self, claim_id: str) -> list:
        """
        Get complete audit trail for a claim.
        
        Args:
            claim_id: The claim to get logs for
            
        Returns:
            List of audit log entries in chronological order
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM audit_logs
            WHERE claim_id = ?
            ORDER BY created_at ASC
        """, (claim_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]


    # ========================================================================
    # POLICY OPERATIONS
    # ========================================================================

    def save_policy(self, policy_id: str, policy_name: str, covered_items: list,
                    excluded_items: list, requires_receipt: bool, repair_days: int) -> str:
        """
        Save a warranty policy to database.
        
        Args:
            policy_id: Unique policy ID
            policy_name: Name of policy
            covered_items: List of covered items
            excluded_items: List of excluded items
            requires_receipt: Boolean
            repair_days: Integer
            
        Returns:
            policy_id
        """
        # Convert lists to JSON
        covered_json = json.dumps(covered_items)
        excluded_json = json.dumps(excluded_items)
        timestamp = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO policies (policy_id, policy_name, covered_items_json, excluded_items_json, requires_receipt, repair_days, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (policy_id, policy_name, covered_json, excluded_json, requires_receipt, repair_days, timestamp))
        
        conn.commit()
        conn.close()
        
        return policy_id


    def get_policy(self, policy_id: str) -> dict:
        """
        Retrieve a policy by ID.
        
        Args:
            policy_id: The policy to retrieve
            
        Returns:
            Dictionary with policy data (lists are converted back from JSON)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM policies WHERE policy_id = ?", (policy_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            data = dict(row)
            # Convert JSON back to lists
            data['covered_items'] = json.loads(data['covered_items_json'])
            data['excluded_items'] = json.loads(data['excluded_items_json'])
            return data
        return None


    # ========================================================================
    # EVALUATION METRIC OPERATIONS
    # ========================================================================

    def save_metric(self, metric_id: str, metric_name: str, metric_value: float,
                    expected_value: float = None, test_type: str = None, description: str = None) -> str:
        """
        Save an evaluation metric.
        
        Args:
            metric_id: Unique metric ID
            metric_name: Name of metric (accuracy, precision, recall, etc.)
            metric_value: The value (0.92, 0.87, etc.)
            expected_value: Target value
            test_type: Type of test (golden_set, regression, production)
            description: Description
            
        Returns:
            metric_id
        """
        timestamp = datetime.utcnow()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO evaluation_metrics (metric_id, metric_name, metric_value, expected_value, test_type, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (metric_id, metric_name, metric_value, expected_value, test_type, description, timestamp))
        
        conn.commit()
        conn.close()
        
        return metric_id


    def get_metrics_summary(self, test_type: str = None) -> dict:
        """
        Get summary of evaluation metrics.
        
        Args:
            test_type: Optional filter by test type
            
        Returns:
            Dictionary with metric statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT metric_name, AVG(metric_value) as avg_value, COUNT(*) as count FROM evaluation_metrics WHERE 1=1"
        params = []
        
        if test_type:
            query += " AND test_type = ?"
            params.append(test_type)
        
        query += " GROUP BY metric_name"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return {row[0]: {"avg": row[1], "count": row[2]} for row in rows}


    # ========================================================================
    # STATISTICS & UTILITY
    # ========================================================================

    def get_stats(self) -> dict:
        """
        Get overall database statistics.
        
        Returns:
            Dictionary with stats (total_claims, approval_rate, etc.)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get total claims
        cursor.execute("SELECT COUNT(*) FROM claims")
        total = cursor.fetchone()[0]
        
        # Get approved claims
        cursor.execute("SELECT COUNT(*) FROM claims WHERE decision = 'APPROVE'")
        approved = cursor.fetchone()[0]
        
        # Get rejected claims
        cursor.execute("SELECT COUNT(*) FROM claims WHERE decision = 'REJECT'")
        rejected = cursor.fetchone()[0]
        
        # Get audit logs count
        cursor.execute("SELECT COUNT(*) FROM audit_logs")
        logs = cursor.fetchone()[0]
        
        # Get policies count
        cursor.execute("SELECT COUNT(*) FROM policies")
        policies = cursor.fetchone()[0]
        
        conn.close()
        
        approval_rate = (approved / total * 100) if total > 0 else 0
        
        return {
            "total_claims": total,
            "approved_claims": approved,
            "rejected_claims": rejected,
            "approval_rate": round(approval_rate, 2),
            "total_audit_logs": logs,
            "total_policies": policies
        }


# ============================================================================
# HELPER FUNCTION - Singleton Pattern
# ============================================================================

def get_db(db_path: str = "surebright.db") -> SureBrightDB:
    """
    Get or create database instance (singleton).
    
    This ensures you only have one database connection throughout your app.
    """
    if not hasattr(get_db, 'instance'):
        get_db.instance = SureBrightDB(db_path)
    return get_db.instance


# ============================================================================
# TESTING - Run this to verify everything works
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING DATABASE.PY")
    print("="*60 + "\n")
    
    # Create/connect to database
    db = SureBrightDB("test_surebright.db")
    
    # Test 1: Save a claim
    print("Test 1: Save a claim")
    claim_id = db.save_claim("John Doe", "Screen Damage", 500.0, "Cracked screen")
    print(f"  ✅ Saved claim: {claim_id}\n")
    
    # Test 2: Log an action
    print("Test 2: Log an action")
    log_id = db.log_action(
        claim_id=claim_id,
        node_name="coverage_check_node",
        action="Checked coverage",
        status="SUCCESS",
        input_data={"claim_type": "Screen Damage", "amount": 500},
        output_data={"decision": "APPROVE", "confidence": 0.92},
        duration_ms=145.5
    )
    print(f"  ✅ Logged action: {log_id}\n")
    
    # Test 3: Get claim
    print("Test 3: Get claim")
    claim = db.get_claim(claim_id)
    print(f"  ✅ Retrieved claim: {claim['claim_id']} - {claim['customer_name']}\n")
    
    # Test 4: Update claim
    print("Test 4: Update claim")
    db.update_claim(claim_id, "APPROVE", 500.0, "Screen covered under warranty")
    print(f"  ✅ Updated claim\n")
    
    # Test 5: Get audit trail
    print("Test 5: Get audit trail")
    trail = db.get_audit_trail(claim_id)
    print(f"  ✅ Retrieved {len(trail)} audit logs\n")
    
    # Test 6: Save policy
    print("Test 6: Save policy")
    policy_id = db.save_policy(
        policy_id=f"POLICY-{uuid.uuid4().hex[:8]}",
        policy_name="Standard Phone Warranty",
        covered_items=["Screen", "Battery", "Speaker"],
        excluded_items=["Water Damage", "Theft"],
        requires_receipt=True,
        repair_days=14
    )
    print(f"  ✅ Saved policy: {policy_id}\n")
    
    # Test 7: Save metric
    print("Test 7: Save metric")
    db.save_metric(
        metric_id=str(uuid.uuid4()),
        metric_name="accuracy",
        metric_value=0.92,
        expected_value=0.95,
        test_type="golden_set"
    )
    print(f"  ✅ Saved metric\n")
    
    # Test 8: Get stats
    print("Test 8: Get statistics")
    stats = db.get_stats()
    print(f"  ✅ Database stats:")
    for key, value in stats.items():
        print(f"     {key}: {value}")
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60 + "\n")