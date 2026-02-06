"""
DRE API - The Bridge
FastAPI server that connects the Brain to the UI via WebSocket
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
import json
from datetime import datetime
from .audit_logger import AuditLogger
from guardian.core.config import get_config

logger = logging.getLogger("DRE_Bridge")

app = FastAPI(title="DRE Guardian API")

# CORS for production static dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static assets FIRST - before any route definitions
# This ensures /assets/* is handled before any catch-all routes
import sys
from pathlib import Path

class PathManager:
    """
    Virtual File System resolver for frozen-aware asset routing.
    
    Handles path resolution differences between:
    - Frozen mode (PyInstaller): Assets in sys._MEIPASS
    - Development mode: Assets in ../dashboard/dist
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.is_frozen = getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')
        self._meipass = getattr(sys, '_MEIPASS', None) if self.is_frozen else None
        self._initialized = True
        
        logger.info(f"PathManager: frozen={self.is_frozen}, _MEIPASS={self._meipass}")
    
    @property
    def dashboard_dist(self) -> Path:
        """Get dashboard dist directory path"""
        if self.is_frozen:
            return Path(self._meipass) / "dashboard" / "dist"
        else:
            bundle_dir = Path(__file__).resolve().parent.parent
            app_dir = bundle_dir.parent
            return app_dir / "dashboard" / "dist"
    
    @property
    def dashboard_assets(self) -> Path:
        """Get dashboard assets directory path"""
        return self.dashboard_dist / "assets"
    
    @property
    def dashboard_index(self) -> Path:
        """Get dashboard index.html path"""
        return self.dashboard_dist / "index.html"
    
    def exists(self) -> bool:
        """Check if dashboard files exist"""
        return self.dashboard_index.exists()

# Initialize path manager
path_manager = PathManager()

def _get_dashboard_dist():
    """Get dashboard dist path - uses PathManager"""
    return path_manager.dashboard_dist

def _get_dashboard_assets():
    """Get dashboard assets path for mounting"""
    return path_manager.dashboard_assets

_assets_dir = _get_dashboard_assets()
if _assets_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(_assets_dir), html=False), name="assets")
    logger.info(f"✓ Dashboard assets mounted from {_assets_dir}")
else:
    logger.warning(f"✗ Assets not found at {_assets_dir}")

# Active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Push state to all connected UIs"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
                logger.info("Broadcasted governance state to UI")
            except Exception as e:
                logger.error(f"Failed to send to WebSocket: {e}")

manager = ConnectionManager()

# Lazy initialization helpers
def get_audit_logger():
    """Get audit logger - called at runtime, not module load time"""
    config = get_config()
    return AuditLogger(str(config.audit_log_path))

# Models
class OverrideRequest(BaseModel):
    assertion_ids: List[str]
    justification: str
    signature: str
    timestamp: str
    signature_hash: str  # SHA-256 hash for non-repudiation

class GovernanceState(BaseModel):
    """
    Zero-Leakage payload - ONLY distributions and gate status
    NO raw Excel values, NO baselines, NO sensitive data
    """
    assertions: List[Dict[str, Any]]
    conflict_pair: Optional[List[str]] = None

# WebSocket endpoint - PUSH ONLY
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Keep connection alive, only send when Brain pushes
        while True:
            # Wait for ping to keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Override endpoint
@app.post("/override")
async def submit_override(request: OverrideRequest):
    """
    Records override request - DOES NOT clear HALTs
    The Brain evaluates this against policy
    """
    logger.warning(
        f"Override request received:\n"
        f"  Assertions: {request.assertion_ids}\n"
        f"  Signature: {request.signature}\n"
        f"  Hash: {request.signature_hash[:16]}...\n"
        f"  Justification: {request.justification[:100]}..."
    )
    
    # Validate Monitor instance is available
    if monitor_instance is None:
        logger.error("Monitor instance not registered with Bridge")
        return {
            "status": "error",
            "message": "Monitor not available - command ingress failed",
            "timestamp": datetime.now().isoformat()
        }, 503
    
    # Forward command to Monitor (authoritative state owner)
    try:
        monitor_instance.register_bypass(
            assertion_ids=request.assertion_ids,
            justification=request.justification,
            signature=request.signature,
            signature_hash=request.signature_hash,
            timestamp=request.timestamp,
            expiry_seconds=3600  # 1 hour default
        )
    except ValueError as e:
        # Monitor rejected bypass (e.g., assertion not in HALT)
        logger.warning(f"Bypass rejected by Monitor: {e}")
        return {
            "status": "rejected",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }, 400
    except Exception as e:
        # Unexpected error - fail loudly
        logger.error(f"Bypass command failed: {e}")
        raise
    
    # Log to audit trail after successful registration
    audit_logger = get_audit_logger()
    for assertion_id in request.assertion_ids:
        audit_logger.log_event(
            event_type="OVERRIDE_REQUEST",
            assertion_id=assertion_id,
            details={
                "justification": request.justification,
                "timestamp": request.timestamp,
                "signature_hash": request.signature_hash,
                "hash_input": f"{request.justification[:50]}|{request.signature}|{request.timestamp}"
            },
            user=request.signature,
            severity="WARN"
        )
    
    return {
        "status": "accepted",
        "message": "Bypass registered in Monitor authoritative state",
        "timestamp": datetime.now().isoformat()
    }

# Audit endpoints (Three-Tiered Model)
@app.get("/api/audit/recent")
async def get_recent_audit(limit: int = 50, offset: int = 0):
    """
    Hot Window: Returns recent audit events for Dashboard
    Scope: Last 24 hours or current session
    Purpose: Show active delta since last model open
    """
    config = get_config()
    log_path = config.audit_log_path
    
    logger.debug(f"Checking audit log at: {log_path}")
    
    if not log_path.exists():
        logger.warning(f"Audit log not found at {log_path}")
        return {"events": [], "total": 0}
    
    # Read all events
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    logger.debug(f"Read {len(events)} total events from audit log")
    
    # Filter: last 24 hours
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent = []
    
    for e in events:
        try:
            event_time = datetime.fromisoformat(e["timestamp"])
            if event_time > cutoff:
                recent.append(e)
        except (ValueError, KeyError) as err:
            logger.warning(f"Failed to parse timestamp: {e.get('timestamp', 'missing')} - {err}")
            # Include it anyway if timestamp parsing fails
            recent.append(e)
    
    logger.debug(f"{len(recent)} events in last 24 hours")
    
    # Sort by timestamp - newest first (reverse chronological)
    recent.sort(key=lambda e: e["timestamp"], reverse=True)
    
    # Pagination
    paginated = recent[offset:offset + limit]
    
    return {
        "events": paginated,
        "total": len(recent),
        "limit": limit,
        "offset": offset
    }

@app.get("/api/audit/summary")
async def get_audit_summary():
    """
    State Checkpointing: Returns aggregated metrics
    Purpose: "3 Stability Breaches in the last 10 saves"
    """
    config = get_config()
    log_path = config.audit_log_path
    
    if not log_path.exists():
        return {
            "total_events": 0,
            "by_severity": {"INFO": 0, "WARN": 0, "CRITICAL": 0},
            "halt_count": 0,
            "override_count": 0,
            "last_24hrs": 0
        }
    
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    # Aggregate metrics
    from datetime import datetime, timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    
    severity_count = {"INFO": 0, "WARN": 0, "CRITICAL": 0}
    halt_count = 0
    override_count = 0
    last_24hrs = 0
    
    for event in events:
        # Count by severity
        severity = event.get("severity", "INFO")
        severity_count[severity] = severity_count.get(severity, 0) + 1
        
        # Count specific event types
        if event["event_type"] == "HALT":
            halt_count += 1
        if event["event_type"] == "OVERRIDE_REQUEST":
            override_count += 1
        
        # Count last 24hrs
        if datetime.fromisoformat(event["timestamp"]) > cutoff:
            last_24hrs += 1
    
    return {
        "total_events": len(events),
        "by_severity": severity_count,
        "halt_count": halt_count,
        "override_count": override_count,
        "last_24hrs": last_24hrs
    }

# Global state storage
current_governance_state: Optional[Dict[str, Any]] = None

# Monitor instance for command ingress
monitor_instance = None

# Trigger HALT UI (called by Brain)
async def trigger_halt_ui(governance_state: Dict[str, Any]):
    """
    Called by the Brain when a HALT occurs
    Stores state and broadcasts to all connected UIs
    """
    global current_governance_state
    current_governance_state = governance_state
    await manager.broadcast(governance_state)
    logger.critical("HALT state pushed to UI")

# Get current governance state (for polling)
@app.post("/api/governance/state")
async def update_governance_state(state: dict):
    """Update governance state from monitor"""
    global current_governance_state
    current_governance_state = state
    await manager.broadcast(state)
    return {"status": "updated"}

@app.get("/api/governance/state")
async def get_governance_state():
    """Returns the current governance state"""
    if current_governance_state is None:
        return {"assertions": [], "conflict_pair": None}
    return current_governance_state

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "active",
        "connections": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }

# Serve index.html for root
@app.get("/")
async def root():
    """Serve dashboard index.html"""
    dashboard_dist = _get_dashboard_dist()
    index_file = dashboard_dist / "index.html"
    if index_file.exists():
        return FileResponse(
            str(index_file),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return {"error": "Dashboard not built", "path": str(index_file)}, 503

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
