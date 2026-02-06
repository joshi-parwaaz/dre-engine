"""
DRE Main Entry Point - Production Server
Uvicorn runs in main thread, monitor in background
"""
from guardian.watcher.watcher import DREWatcher
from guardian.core.loader import ManifestLoader
from guardian.core.ingestor import ExcelIngestor
from guardian.core.brain import GateEngine
from guardian.api.audit_logger import AuditLogger
from guardian.core.config import get_config
import logging
import webbrowser
import sys
import socket
from threading import Thread
from pathlib import Path

logger = logging.getLogger("DRE_Guardian")
config = get_config()
audit_logger = AuditLogger(str(config.audit_log_path))

# Frozen mode detection for ASCII-safe output
_is_frozen = getattr(sys, 'frozen', False) and sys.platform == 'win32'

def _print(msg: str):
    """Print message - ASCII-safe in frozen mode"""
    if _is_frozen:
        # Replace Unicode with ASCII equivalents
        msg = msg.replace('→', '->').replace('✓', '[OK]').replace('✗', '[X]')
    print(msg)


def run_production_server(manifest_path: str = None, auto_open_browser: bool = True):
    """
    Production server launcher.
    
    Architecture:
    - Daemon thread: File watcher/monitor (background)
    - Main thread: Uvicorn HTTP server (blocking, handles Ctrl+C)
    
    Args:
        manifest_path: Optional path to manifest.json
        auto_open_browser: Whether to open browser automatically
    """
    _print("→ Starting governance monitor...")
    from guardian.monitor import DREMonitor
    
    monitor = DREMonitor(manifest_path=manifest_path, enable_dashboard=False)
    
    def run_monitor():
        try:
            monitor.run()
        except Exception as e:
            logger.error(f"Monitor thread error: {e}", exc_info=True)
    
    monitor_thread = Thread(target=run_monitor, daemon=True, name="MonitorThread")
    monitor_thread.start()
    _print("✓ Monitor started")
    
    # Find available port
    port = _find_available_port()
    if port is None:
        _print("✗ Ports 8000-8002 are all in use")
        _print("  Close other applications and try again")
        sys.exit(1)
    
    _print(f"→ Starting dashboard on port {port}...")
    
    dashboard_url = f"http://127.0.0.1:{port}"
    _print(f"✓ Dashboard running at {dashboard_url}")
    
    # Auto-open browser before blocking server starts
    if auto_open_browser:
        try:
            webbrowser.open(dashboard_url)
        except Exception as e:
            logger.warning(f"Could not open browser: {e}")
    
    _print("\nPress Ctrl+C to stop\n")
    
    # Run uvicorn in main thread (blocking, handles signals properly)
    try:
        import uvicorn
        from guardian.api.bridge import app
        
        uvicorn.run(
            app,
            host='127.0.0.1',
            port=port,
            log_level="warning",
            access_log=False,
        )
    except KeyboardInterrupt:
        pass
    
    _print("\nShutting down...")
    sys.exit(0)


def _find_available_port(start_port=8000, max_attempts=3):
    """Find an available port to bind to."""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


async def trigger_halt_ui(governance_state):
    """
    Triggers the UI when a HALT occurs
    Opens browser and pushes state via WebSocket
    """
    try:
        from guardian.api.bridge import trigger_halt_ui as push_to_ui
        await push_to_ui(governance_state)
        logger.info("UI state pushed to dashboard")
    except Exception as e:
        logger.error(f"Failed to trigger UI: {e}")


def run_governance_cycle(filepath):
    try:
        # 1. Load Contract
        from guardian.core.config import get_config
        config = get_config()
        manifest_path = str(config.manifest_path)
        manifest = ManifestLoader.load(manifest_path)
        
        # 2. Ingest Data (Handling Excel Locks)
        ingestor = ExcelIngestor(manifest, manifest_path)
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


if __name__ == "__main__":
    pass
