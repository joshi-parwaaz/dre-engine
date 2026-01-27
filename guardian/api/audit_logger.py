import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

# Professional audit severity levels (INFO < WARN < CRITICAL)
SeverityLevel = Literal["INFO", "WARN", "CRITICAL"]

class AuditLogger:
    def __init__(self, log_path: str = "../project_space/audit_log.jsonl"):
        self.log_path = Path(log_path)
        self.session_id = self._generate_session_id()

    def _generate_session_id(self) -> str:
        """Generate unique session ID for grouping events in 24hr windows"""
        return datetime.now(timezone.utc).strftime("%Y%m%d-%H")

    def log_event(
        self, 
        event_type: str, 
        assertion_id: str, 
        details: dict, 
        user: str = "SYSTEM",
        severity: SeverityLevel = "INFO"
    ):
        """
        Commits a governance event to the persistent ledger.
        
        Severity Levels:
        - INFO: Formula checks, validation passes, routine operations
        - WARN: Manual overrides, stability warnings, non-critical issues
        - CRITICAL: HALT events, security breaches, data corruption
        
        Fulfills the 'Auditable Override' requirement.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "session_id": self.session_id,
            "severity": severity,
            "event_type": event_type, # e.g., "HALT", "BYPASS", "STABILITY_SHOCK"
            "assertion_id": assertion_id,
            "user_anchor": user,
            "details": details
        }
        
        # Append-only mode for data integrity
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

# Example Entry for a Bypass:
# {
#   "timestamp": "2026-01-22T12:00:00Z",
#   "event_type": "MANUAL_BYPASS",
#   "assertion_id": "uuid-8823",
#   "user_anchor": "Director of Supply Chain",
#   "details": {"justification": "Global shipping delay accounted for in buffer"}
# }