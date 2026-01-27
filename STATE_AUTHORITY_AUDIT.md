# State Authority Audit - DRE Guardian
**Audit Date**: January 27, 2026  
**Scope**: HALT lifecycle and authoritative state storage

---

## Section 1: Authoritative State Location

### Primary State Variables

**1. `global_halt` (local variable in `monitor.py:238`)**
- **Type**: Boolean, local variable (not global, not class attribute, not persisted)
- **Scope**: Function-scoped in `run_governance_cycle()`
- **Lifetime**: Created each governance cycle, destroyed at function exit
- **Initial value**: `False` (line 238)
- **Authority**: None. This is a **computed temporary flag**, not authoritative state.

**2. `self.last_status` (instance variable in `DREMonitor` class)**
- **Type**: String (`"HALT"`, `"PASS"`, `"IDLE"`, or `"ERROR: ..."`)
- **Location**: `monitor.py:43` (initialization), mutated at line 288
- **Scope**: Instance attribute of `DREMonitor` class
- **Lifetime**: Lives as long as monitor process runs, **lost on restart**
- **Authority**: Display-only. Used exclusively for TUI rendering (lines 104, 153). Never read for control flow decisions.

**3. `bridge_module.current_governance_state` (global variable in `api/bridge.py:236`)**
- **Type**: `Optional[Dict[str, Any]]`
- **Location**: `guardian/api/bridge.py:236`
- **Structure**:
  ```python
  {
      "status": "HALT" | "PASS",
      "assertions": [...],
      "conflict_pair": None,
      "last_updated": ISO timestamp
  }
  ```
- **Scope**: Module-global variable
- **Lifetime**: Lives as long as FastAPI process runs, **lost on restart**
- **Write points**: Line 306 in `monitor.py` (sets entire dict)
- **Read points**: Line 253 in `bridge.py` via `/api/governance/state` endpoint
- **Authority**: **This is the source of truth for dashboard display.** Dashboard polls this every 2 seconds.

**4. Audit log (`audit_log.jsonl`)**
- **Type**: Append-only JSONL file
- **Location**: `project_space/audit_log.jsonl`
- **Persistence**: Survives process restarts
- **Write points**: 
  - `monitor.py:255-267` (HALT events)
  - `bridge.py:101-112` (OVERRIDE_REQUEST events)
- **Authority**: **Historical record only.** Never read to determine current system state. Events are write-only.

### State Authority Verdict

**Fragmented authority with no single source of truth.**

- **Runtime state**: `current_governance_state` global variable (ephemeral, in-memory)
- **Display state**: `self.last_status` string (ephemeral, TUI-only)
- **Historical record**: `audit_log.jsonl` (persistent but never queried for state)
- **No persistence layer for current HALT status**
- **No state reconciliation mechanism**
- **No checkpoint/recovery system**

On process restart, all knowledge of current HALT state is lost. System recomputes from scratch by re-evaluating Excel file.

---

## Section 2: HALT State Transition Trace

### 2.1: HALT Creation Path

**Trigger Condition** (monitor.py:252-253):
```python
if "HALT" in [g1["status"], g2["status"], g4["status"]]:
    global_halt = True
```

**What sets HALT**:
1. Gate functions return dicts with `"status": "HALT"` or `"status": "PASS"`
2. Located in `core/brain.py`:
   - `gate_1_freshness()`: lines 28-56
   - `gate_2_stability()`: lines 58-110
   - `gate_4_structure()`: lines 141-163
3. Any gate returning `"HALT"` triggers the condition

**State mutation sequence** (monitor.py:238-310):
```
Line 238: global_halt = False          # Initialize local var
Line 253: global_halt = True           # Set if any gate fails
Line 288: self.last_status = "HALT"    # Set display string
Line 306: bridge_module.current_governance_state = {...}  # Set global dict with "status": "HALT"
```

**Side effects**:
- Line 255-267: Write to audit_log.jsonl (append-only, never read back)
- Line 289: Increment `self.halt_count` (metric counter)
- Line 309-311: Open web browser to http://localhost:5173

**Storage locations after HALT**:
- ✅ `current_governance_state["status"] = "HALT"` (in-memory global)
- ✅ `self.last_status = "HALT"` (instance var)
- ✅ Audit log entry with `"event_type": "HALT"` (persistent file)
- ❌ `global_halt` **is destroyed** when function exits (local variable)

### 2.2: HALT Bypass Path

**User Action**: Click "Bypass HALT" button in dashboard

**Frontend execution** (dashboard/src/App.tsx:549-618):
```typescript
// Line 549: User clicks "Bypass HALT" button
// Line 584-591: User enters justification + signature
// Line 593-596: Compute SHA-256 hash
// Line 598-612: POST to /override endpoint
```

**Backend execution** (api/bridge.py:82-115):
```python
@app.post("/override")
async def submit_override(request: OverrideRequest):
    # Line 88-96: Log warning to console
    # Line 99-112: Write to audit_log.jsonl
    # Line 114: # TODO: Notify Brain for policy evaluation
    # Line 116-120: Return success response
```

**State mutations in override endpoint**:
1. **None.**

**Side effects in override endpoint**:
- Logger warning (line 88-96): Ephemeral console output
- Audit log write (line 101-112): Persistent JSONL append
- HTTP response (line 116-120): Confirmation message to frontend

**Variables examined**:
- ❌ Does NOT read `current_governance_state`
- ❌ Does NOT modify `current_governance_state`
- ❌ Does NOT call any Brain function
- ❌ Does NOT trigger governance cycle re-run
- ❌ Does NOT clear any HALT flag

### 2.3: State Check After Bypass

**Frontend behavior** (App.tsx:147-170):
```typescript
// Line 150-163: Polling continues every 2s
// Fetches GET /api/governance/state
// Receives same state object with "status": "HALT"
// Re-renders UI with HALT still showing
```

**Backend response** (bridge.py:250-256):
```python
@app.get("/api/governance/state")
async def get_governance_state():
    if current_governance_state is None:
        return {"assertions": [], "conflict_pair": None}
    return current_governance_state  # Returns UNCHANGED state
```

**State value after bypass**:
- `current_governance_state["status"]` remains `"HALT"`
- `self.last_status` remains `"HALT"`
- Audit log contains both HALT and OVERRIDE_REQUEST entries
- **No state transition occurred**

### 2.4: Next Governance Cycle

**When next file change triggers governance cycle** (monitor.py:230-310):
```python
# Line 238: global_halt = False  # Fresh local var, previous value forgotten
# Line 240-252: Re-run gates on current Excel state
# Line 253: global_halt = True   # Set again if gates still fail
# Line 288: self.last_status = "HALT"  # Set again
# Line 306: current_governance_state updated with fresh evaluation
```

**Bypass has no effect**:
- Gates re-evaluate from scratch
- No memory of bypass request
- No exemption logic
- If Excel values still violate gates, HALT recurs

**Only way HALT clears**:
1. User manually edits Excel to satisfy gate conditions
2. Next governance cycle runs
3. All gates return `"PASS"`
4. `global_halt` stays `False`
5. `current_governance_state["status"]` set to `"PASS"`

---

## Section 3: Verdict

**After a user clicks bypass, what exact line of code changes the system from HALT = true to HALT = false?**

**No such line exists.**

**HALT bypass does not mutate authoritative state.**

The override endpoint is a logging facade. It writes an audit entry, returns a confirmation message, and terminates. The `current_governance_state` global variable, which the dashboard polls to display HALT status, is never touched by the override code path. The TODO comment at line 114 (`# TODO: Notify Brain for policy evaluation`) marks where actual bypass logic should exist but does not.

State transitions occur **only** through governance cycle re-evaluation. The bypass button provides the illusion of control but performs no state mutation. Users who click "Bypass HALT" receive a green checkmark and a confirmation message, then watch the dashboard continue to show HALT status because the authoritative state (`current_governance_state["status"]`) remains unchanged at `"HALT"`.

This is security theater masquerading as governance override.

**Side effects that are not state changes**:
1. **Audit log append** (bridge.py:101-112): Write-only historical record, never consulted for current state
2. **Logger warning** (bridge.py:88-96): Ephemeral console output, disappears on scroll
3. **SHA-256 hash computation** (App.tsx:593-596): Computed in frontend, sent to backend, logged, never verified
4. **HTTP 200 response** (bridge.py:116-120): Confirmation message, no operational effect
5. **Modal close** (App.tsx:614): UI animation, no backend state change
6. **Success toast notification** (App.tsx:615-618): User feedback, cosmetic only

All six are **presentation-layer artifacts** with zero impact on system behavior. The HALT state persists unchanged until the next governance cycle re-evaluates Excel data and gates return PASS.
