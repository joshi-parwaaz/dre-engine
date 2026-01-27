# Pre-Production Reality Check - DRE Guardian

## Executive Summary

**Verdict: NOT production-ready. Ship-blocking issues exist.**

This is a functional prototype with critical gaps in core logic, silent failure modes, and untested assumptions. It will work for demos and single-user testing but will break under real-world conditions.

**Timeline to production**: 2-4 days of focused work on critical issues.

---

## What This System Actually Does (Not What It Claims)

### Real End-to-End Behavior

1. **File Watcher** monitors Excel file (project_space/*.xlsx)
2. **On Excel save**: Debounced callback triggers governance cycle (0.9s delay)
3. **Governance cycle**:
   - Reads Excel file (2 passes: data + formulas)
   - Runs 3 gates (Gate 3 never runs - see below)
   - Computes drift as `abs(current - baseline) / range`
   - Sets global HALT flag if any gate fails
   - Writes to audit_log.jsonl
   - Pushes state to global variable for dashboard
4. **Dashboard polls** that global variable every 2s
5. **User clicks bypass** → Hash computed, logged to audit, **but HALT state unchanged**

### What Is Stubbed/Incomplete

**Critical:**

1. **Gate 3 (Convergence) NEVER RUNS**
   - Location: `monitor.py:243-246`
   - Code: Gates 1, 2, 4 run. Gate 3 is missing.
   - Manifesto claims "4 gates" - only 3 execute.
   - **This is a lie to users.**

2. **Override Bypass Does Nothing**
   - Location: `api/bridge.py:111`
   - Code: `# TODO: Notify Brain for policy evaluation`
   - User clicks "Bypass HALT", pays SHA-256 hash, gets confirmation.
   - **HALT state never clears. System stays in HALT forever.**
   - Button is theater. No actual bypass mechanism exists.

3. **Conflict Detection Disabled**
   - Location: `monitor.py:303`
   - Code: `"conflict_pair": None`
   - Location: `main.py:93`
   - Code: `# TODO: Detect conflicts`
   - Dashboard shows "Departmental Alignment" component.
   - **Never populates. Dead code.**

4. **PERT Distribution Overlap Calculation is Wrong**
   - Location: `brain.py:92`
   - Code: `# Calculate overlap integral (simplified)`
   - Comment: `# In practice, you'd compute the actual distribution overlap`
   - **Current logic**: `drift = abs(current_norm - baseline_norm)`
   - **This is NOT an overlap integral.** It's just normalized distance.
   - Beta distribution parameters computed but never used.
   - **Math doesn't match documentation.**

**Non-Critical But Dishonest:**

5. **Governance Velocity Shows Wrong Metrics**
   - Shows "cycles" vs "HALTs" vs "overrides"
   - Only HALTs are logged to audit_log.jsonl
   - **Cycles never logged** - metric is always 0 or nonsense.

6. **Digital Signature "Verification"**
   - Tool exists: `tools/verify_signature.py`
   - **Never called automatically. User must remember to run it.**
   - Audit trail can be tampered with. Verification is optional.

---

## System Architecture (As Implemented)

### Component Responsibilities

**Guardian (Python)**
- `core/brain.py`: Gate logic (168 lines)
  - Gate 1: Freshness check (SLA days)
  - Gate 2: Fake PERT overlap (actually just drift %)
  - Gate 3: Placeholder (returns SKIP always)
  - Gate 4: Formula hash comparison
- `core/ingestor.py`: Excel file reader with retry logic
- `watcher/watcher.py`: File system monitor with mutex lock
- `monitor.py`: Rich TUI + governance cycle orchestration (384 lines)
- `api/bridge.py`: FastAPI server (269 lines)
  - REST endpoints + WebSocket (unused)
  - Global variable state storage
  - Audit log reader
- `api/audit_logger.py`: Append-only JSONL writer (80 lines)

**Dashboard (React + TypeScript)**
- `App.tsx`: Main component (898 lines post-fix)
  - 3 views: Leadership, HALT, Assertions
  - Polling every 2s (timestamp check prevents unnecessary refreshes)
  - Bypass modal with SHA-256 hashing
- `components/GovernanceVelocity.tsx`: 24-hour timeline (300 lines)
- `components/EpistemicHealthMap.tsx`: Assertion health cards (171 lines)
- `components/ConflictCollisionMap.tsx`: Conflict detector (dead code)

### Data Flow

```
Excel Save
  ↓
File Watcher (0.9s debounce, mutex lock)
  ↓
run_governance_cycle()
  ↓
ExcelIngestor.read_data() [2 passes: values + formulas]
  ↓
For each assertion:
  - gate_1_freshness()
  - gate_2_stability() [WRONG MATH]
  - [gate_3 SKIPPED]
  - gate_4_structure()
  ↓
If any HALT:
  - audit_logger.log_event("HALT", ...)
  - global_halt = True
  ↓
bridge_module.current_governance_state = {...}  [GLOBAL VARIABLE]
  ↓
Dashboard polls every 2s
  ↓
React setState() → UI update
```

**Critical Coupling:**
- Dashboard depends on global variable in `api/bridge.py`
- No persistence layer - state evaporates on restart
- Audit log is only persistent storage
- WebSocket exists but is never used for state push

### State Management

**Created:**
- `monitor.py`: In-memory state (last_status, total_checks, halt_count, current_assertions)
- `api/bridge.py`: Global variable `current_governance_state`

**Mutated:**
- Every governance cycle overwrites global state
- Rich TUI updates every 2s if state changes (tuple comparison)
- Dashboard polls, compares timestamp, updates if changed

**Persisted:**
- Only `audit_log.jsonl` (append-only JSONL)
- No database
- No checkpoint files
- Restart = lose all in-memory state

**Tight Coupling:**
- Monitor directly imports `api.bridge` and mutates global var
- Dashboard hardcodes `http://localhost:8000`
- CLI commands hardcode `../project_space/` paths
- No dependency injection, no interfaces, no mocks

---

## Critical Unknowns and Unproven Assumptions

### Never Validated With Real Data

1. **Large Excel files (>1MB, >50 assertions)**
   - openpyxl loads entire workbook into memory
   - Two passes (data + formulas) = 2x memory footprint
   - **Assumption**: Files are small (<100 cells monitored)
   - **Risk**: 500-cell financial model could OOM

2. **Excel file locks during read**
   - Retry logic exists (5 attempts, exponential backoff)
   - **Assumption**: Excel releases lock within ~15 seconds
   - **Risk**: If user keeps file open, monitor deadlocks forever
   - No timeout. No user feedback. Silent hang.

3. **Rapid Excel saves (autosave, macro writes)**
   - Debounce: 0.9s
   - Mutex lock prevents concurrent governance cycles
   - **Assumption**: Governance cycle completes < 0.9s
   - **Risk**: If cycle takes 2s, queue builds up in memory
   - No queue depth limit. No backpressure. Potential memory leak.

4. **PERT distribution shapes**
   - Assumes min < mode < max
   - **No validation** in schema loader
   - **Risk**: `mode = 100, min = 200, max = 50` → divide by zero

5. **Baseline values exist**
   - Gate 2 requires `assertion.baseline_value`
   - **No check** if baseline is None
   - **Risk**: `TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'`

6. **Formula hashes are stable**
   - Excel formats formulas differently across versions
   - **Assumption**: `=SUM(A1:A10)` always hashes identically
   - **Risk**: Excel 2019 vs 365 might format differently → false HALTs

7. **Audit log file growth**
   - Append-only, unbounded
   - **Assumption**: <1000 events/day
   - **Risk**: At 1 event/second = 86,400/day = 31M/year
   - No rotation, no archival

8. **Dashboard polling doesn't DOS backend**
   - Poll every 2s = 43,200 requests/day per user
   - **Assumption**: Single user
   - **Risk**: 10 users = 432,000 requests/day. FastAPI can handle, but silly.

---

## Failure Modes (How This System Fails Today)

### Silent Failures

1. **Bypass Button Lies**
   - User clicks "Bypass HALT"
   - Hash computed, logged, confirmation shown
   - **HALT state unchanged**
   - Monitor still shows red, dashboard still blocked
   - **User experience**: "I bypassed it, why is it still red?"
   - **Detection**: None. User must notice manually.

2. **Gate 3 Never Runs**
   - Code exists in `brain.py`
   - Never called in `monitor.py`
   - **User believes** convergence is checked (documentation claims it)
   - **Reality**: No convergence monitoring
   - **Detection**: Read the code. No runtime indication.

3. **PERT Math Wrong**
   - Documentation: "Overlap integral calculation"
   - Code: `drift = abs(current_norm - baseline_norm)`
   - **This is not an integral.** Beta distribution params computed but unused.
   - **User experience**: HALT triggers at unexpected drift values
   - **Detection**: Compare expected overlap vs actual - requires stats knowledge

4. **Conflict Detection Dead**
   - "Departmental Alignment" shown in dashboard
   - Always empty
   - **User experience**: "Why don't I see conflicts?"
   - **Detection**: None. Looks like there are no conflicts.

5. **Audit Log Corruption**
   - No file locking
   - Concurrent writes from monitor + override endpoint = race condition
   - **Result**: Malformed JSON lines
   - **Detection**: `python cli.py audit` crashes with JSONDecodeError

### Noisy Failures (Crashes)

1. **Missing Excel File**
   - Monitor starts before Excel file exists
   - `openpyxl.load_workbook()` → `FileNotFoundError`
   - **Result**: `except Exception as e: self.last_status = f"ERROR: {str(e)[:30]}"`
   - TUI shows truncated error
   - **User experience**: "ERROR: [Errno 2] No such file"
   - **Recovery**: Restart monitor after creating file

2. **Malformed Manifest**
   - Invalid PERT distribution (min > max)
   - Pydantic validation catches it during `ManifestLoader.load()`
   - **Result**: ValidationError, clean traceback
   - **User experience**: Clear error message
   - **Recovery**: Fix manifest, restart

3. **Port 8000 In Use**
   - Backend tries to start FastAPI on 8000
   - Another process holds it
   - **Result**: `uvicorn` error, monitor exits
   - **User experience**: Monitor crashes immediately
   - **Detection**: Terminal shows "Address already in use"
   - **Recovery**: Kill other process or change port (hardcoded)

4. **TypeScript Compilation Error**
   - Dashboard won't build if syntax error
   - **Result**: `npm run build` fails, Vite dev server won't start
   - **User experience**: Dashboard inaccessible
   - **Detection**: Terminal shows TypeScript errors
   - **Recovery**: Fix code, rebuild

### Ghost Processes

1. **Orphaned FastAPI Server**
   - Monitor killed with Ctrl+C
   - FastAPI subprocess may not die
   - **Result**: Port 8000 held, next start fails
   - **Detection**: `netstat` shows process on 8000
   - **Recovery**: Manual `taskkill` or `Stop-Process`

2. **File Watcher Leaks**
   - Observer thread started but not joined properly
   - **Result**: Background thread survives Ctrl+C
   - **Detection**: Python process still in Task Manager
   - **Recovery**: Force kill Python

---

## Production Readiness Verdict

### Ship This Today → Here's What Breaks in Week 1

**Day 1:**
- User bypasses HALT
- HALT stays red forever
- User thinks system is broken, emails you angrily

**Day 2:**
- Finance team's 200-assertion model loads
- Monitor OOMs (out of memory)
- System crashes silently, no data captured

**Day 3:**
- User notices "Departmental Alignment" never shows conflicts
- Loses trust in system
- Stops using it

**Day 4:**
- Excel file locked by another process
- Monitor hangs forever
- TUI frozen, no feedback
- User force-kills it, corruption risk in audit log

**Day 5:**
- Audit log hits 10MB (10,000 events)
- `python cli.py audit` takes 5 seconds to load
- User complains about slowness

**Day 6:**
- User runs verification: `python cli.py verify`
- Tool finds tampering (from race condition corruption)
- User loses confidence in audit trail integrity

**Day 7:**
- PM asks: "How many governance cycles ran this week?"
- Answer: "Unknown - we don't log cycles, only HALTs"
- Metric request cannot be fulfilled

---

## Must Fix Before Real Users

### Ship Blockers (P0)

1. **Implement actual bypass mechanism**
   - Location: `api/bridge.py:111`
   - Action: Add state management to clear HALT
   - Options:
     - Persist override to file, check before HALT display
     - Add "bypass_until" timestamp to assertion
     - Allow manual state reset via API
   - **Without this: Bypass button is a scam.**

2. **Actually run Gate 3 or remove it**
   - Location: `monitor.py:243-246`
   - Action: Either call `gate_3_convergence()` or delete all Gate 3 code
   - **Without this: False advertising. Documentation lies.**

3. **Validate PERT distributions in schema**
   - Location: `core/schema.py` (PertDistribution class)
   - Action: Add Pydantic validator: `min < mode < max`, all positive
   - **Without this: Divide by zero, nonsense results.**

4. **Check baseline_value exists before Gate 2**
   - Location: `brain.py:64`
   - Action: Early return if `assertion.baseline_value is None`
   - **Without this: TypeError crash on fresh assertions.**

5. **Fix or remove "overlap integral" claim**
   - Location: `brain.py:92`
   - Options:
     - Actually compute integral (scipy.stats.beta.cdf)
     - Rename to "normalized drift" and update docs
   - **Without this: Math is wrong, results unpredictable.**

### Critical But Not Blocking (P1)

6. **Add file locking to audit log writes**
   - Location: `api/audit_logger.py:46-49`
   - Action: Use `fcntl.flock()` or `portalocker` library
   - **Without this: Concurrent writes corrupt log.**

7. **Add timeout to Excel file lock retry**
   - Location: `core/ingestor.py:26-29`
   - Action: After 5 retries, raise TimeoutError with user message
   - **Without this: Silent hang if Excel locked.**

8. **Implement or remove conflict detection**
   - Location: `monitor.py:303`
   - Action: Compute PERT overlaps between assertions, populate conflict_pair
   - **Without this: Dead component, misleading UI.**

9. **Log governance cycles to audit**
   - Location: `monitor.py:238-290`
   - Action: `audit_logger.log_event("CYCLE", ...)` on each run
   - **Without this: Can't measure "cycles per day" metric.**

10. **Add max queue depth to file watcher**
    - Location: `watcher/watcher.py:36-40`
    - Action: If timer already pending, don't create new one (already done with cancel)
    - **Current code is OK but undocumented.**

---

## Can Safely Wait

**Not blocking, but should be on roadmap:**

- Audit log rotation (P2)
- WebSocket state push instead of polling (P2)
- Multi-user dashboard concurrency (P2)
- Better TUI error messages (full text, not truncated) (P3)
- Port configuration via env var (P3)
- Historical value tracking for Gate 3 (P3)
- Actual asymmetric key signatures instead of SHA-256 (P4)

---

## Minimum Viable Validation Plan

### Real-World Test Suite (2-4 hours)

**Test 1: Bypass Actually Works**
1. Start monitor with test Excel
2. Trigger HALT (change value outside PERT range)
3. Verify TUI shows HALT
4. Click "Bypass HALT" in dashboard
5. Enter justification + signature
6. **Expected**: HALT clears, TUI shows PASS
7. **Actual**: HALT stays red
8. **Verdict**: FAIL - must fix before production

**Test 2: Large File Performance**
1. Create Excel with 100 assertions (100 cells)
2. Start monitor
3. Measure:
   - Load time (should be <5s)
   - Memory usage (should be <500MB)
   - Governance cycle time (should be <2s)
4. **Pass criteria**: All metrics within bounds
5. **Fail action**: Optimize ingestor or limit assertions

**Test 3: Excel Lock Handling**
1. Open Excel file in Excel application
2. Start monitor
3. Edit cell while file open
4. **Expected**: Monitor waits, shows "File locked" message
5. **Actual**: May hang forever
6. **Pass criteria**: Monitor shows feedback, recovers when lock released

**Test 4: Concurrent Audit Writes**
1. Start monitor
2. Trigger 5 HALTs in rapid succession (edit Excel 5 times fast)
3. While monitor writes, click "Bypass HALT" (writes override)
4. Check audit log: `python cli.py audit`
5. **Expected**: All events readable, no JSONDecodeError
6. **Fail action**: Add file locking

**Test 5: PERT Edge Cases**
1. Manifest with `min=100, mode=50, max=200` (mode < min)
2. Load manifest
3. **Expected**: ValidationError with clear message
4. **Actual**: Passes validation, nonsense results
5. **Fail action**: Add Pydantic validator

**Test 6: Dashboard Offline Resilience**
1. Start monitor (backend running)
2. Kill dashboard (`npm` process)
3. Edit Excel, trigger HALT
4. Monitor should continue working
5. **Pass criteria**: TUI updates, audit log written, no crash

**Test 7: Backend Restart State**
1. Trigger HALT, verify dashboard shows it
2. Restart monitor (Ctrl+C, restart)
3. **Expected**: HALT state lost (in-memory), dashboard shows PASS
4. **Actual**: May vary based on Excel current state
5. **Verdict**: Document behavior - "State is ephemeral"

---

## Evidence Needed for "v0 Usable"

1. ✅ **Bypass works end-to-end** (Test 1 passes)
2. ✅ **No crashes with 50-assertion model** (Test 2 passes)
3. ✅ **Excel lock doesn't deadlock** (Test 3 passes)
4. ✅ **Audit log uncorrupted after 100 events** (Test 4 passes)
5. ✅ **PERT validation catches bad input** (Test 5 passes)
6. ⚠️ **Week-long soak test** (1 week runtime, no crashes)
7. ⚠️ **Real financial model tested** (actual user data, not demo)

**Minimum bar**: Tests 1-5 must pass. Tests 6-7 can be concurrent with early adopter usage.

---

## Final Assessment

**Current State**: Functional prototype, suitable for demos and single-user testing

**Production Readiness**: 60%

**Critical Issues**: 5 ship-blockers identified

**Timeline to Production**:
- Fix ship-blockers: 1-2 days
- Run validation tests: 4 hours
- Soak test with real data: 1 week
- **Total: 2-3 weeks** to ship responsibly

**Confidence If Shipped Today**: 40% - will break under real usage

**Confidence After Fixes**: 85% - acceptable for early adopters with support

---

## Recommendations

1. **Do NOT ship to real users yet.** Fix the 5 ship-blockers first.
2. **Run Test 1 (Bypass) immediately.** This will prove the button is broken.
3. **Pick ONE real financial model** as validation target. Not a synthetic demo.
4. **Document known limitations** in README before any external users.
5. **Set expectations**: This is v0, not v1. It will have issues.
6. **Assign on-call support** for first week - users will hit edge cases.

**Bottom line**: This system has good bones but critical gaps. 2-4 days of focused engineering will make it viable for controlled rollout.
