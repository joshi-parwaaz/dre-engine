"""
DRE API - The Bridge
FastAPI server that connects the Brain to the UI via WebSocket
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import asyncio
from datetime import datetime
from .audit_logger import AuditLogger

logger = logging.getLogger("DRE_Bridge")

app = FastAPI(title="DRE Guardian API")

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
audit_logger = AuditLogger("../project_space/audit_log.jsonl")

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
    from pathlib import Path
    # Get absolute path relative to this file
    log_path = Path(__file__).parent.parent.parent / "project_space" / "audit_log.jsonl"
    
    print(f"🔍 Checking audit log at: {log_path}")
    
    if not log_path.exists():
        print(f"⚠️ Audit log not found at {log_path}")
        return {"events": [], "total": 0}
    
    # Read all events
    events = []
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    print(f"📊 Read {len(events)} total events from audit log")
    
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
            print(f"⚠️ Failed to parse timestamp: {e.get('timestamp', 'missing')} - {err}")
            # Include it anyway if timestamp parsing fails
            recent.append(e)
    
    print(f"📊 {len(recent)} events in last 24 hours")
    
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
    log_path = Path("../project_space/audit_log.jsonl")
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
