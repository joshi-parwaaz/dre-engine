from watcher.watcher import DREWatcher
from core.loader import ManifestLoader
from core.ingestor import ExcelIngestor
from core.brain import GateEngine
from api.audit_logger import AuditLogger
import logging
import asyncio
import webbrowser

logger = logging.getLogger("DRE_Guardian")
audit_logger = AuditLogger("../project_space/audit_log.jsonl")

async def trigger_halt_ui(governance_state):
    """
    Triggers the UI when a HALT occurs
    Opens browser and pushes state via WebSocket
    """
    try:
        from api.bridge import trigger_halt_ui as push_to_ui
        await push_to_ui(governance_state)
        # Open browser to dashboard
        webbrowser.open("http://localhost:5173")
        logger.info("UI triggered and browser opened")
    except Exception as e:
        logger.error(f"Failed to trigger UI: {e}")

def run_governance_cycle(filepath):
    try:
        # 1. Load Contract
        manifest = ManifestLoader.load("../project_space/manifest.json")
        
        # 2. Ingest Data (Handling Excel Locks)
        ingestor = ExcelIngestor(manifest)
        current_state = ingestor.read_data()
        
        # 3. Analyze
        brain = GateEngine(manifest)
        global_halt = False
        report = []

        for assertion in manifest.assertions:
            # Run Gate 1: Freshness
            g1 = brain.gate_1_freshness(assertion)
            # Run Gate 2: Stability
            val = current_state[assertion.id]["value"]
            g2 = brain.gate_2_stability(assertion, val)
            
            # Check for Formula Hijack (Gate 4 - Structural)
            stored_hash = assertion.binding.formula_hash
            current_hash = current_state[assertion.id]["formula_hash"]
            g4 = brain.gate_4_structure(stored_hash, current_hash)

            # Aggregate results
            if "HALT" in [g1["status"], g2["status"], g4["status"]]:
                global_halt = True
                
                # Log HALT event to audit trail (CRITICAL severity)
                halt_details = {
                    "gate_1_freshness": g1,
                    "gate_2_stability": g2,
                    "gate_4_structure": g4
                }
                audit_logger.log_event(
                    event_type="HALT",
                    assertion_id=assertion.id,
                    details=halt_details,
                    user=assertion.owner_role,
                    severity="CRITICAL"
                )
            
            report.append({
                "id": assertion.id,
                "logical_name": assertion.logical_name,
                "gate_status": {
                    "freshness": g1["status"],
                    "stability": g2["status"],
                    "alignment": g4["status"]
                },
                "distribution": {
                    "min": assertion.distribution.min,
                    "mode": assertion.distribution.mode,
                    "max": assertion.distribution.max
                }
            })

        # 4. Act
        if global_halt:
            logger.error("!!! GOVERNANCE HALT: Refusing to validate model output !!!")
            
            # Push state to UI (Zero-Leakage payload)
            governance_state = {
                "assertions": report,
                "conflict_pair": None  # TODO: Detect conflicts
            }
            
            # Trigger UI
            asyncio.run(trigger_halt_ui(governance_state))
        else:
            logger.info("Governance Check: PASS")
            
    except Exception as e:
        logger.error(f"Systemic Failure: {str(e)}")

# This integrates with the Phase 2 Watcher
if __name__ == "__main__":
    # In a real run, we point the watcher to the directory
    # and pass 'run_governance_cycle' as the callback.
    pass