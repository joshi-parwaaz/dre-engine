# DRE Guardian - Complete User Flows

## Flow 1: New User Installing from GitHub

```
1. Download/Clone Repository
   └─> git clone <repo-url> dre-guardian

2. Install Dependencies
   └─> cd dre-guardian
   └─> pip install -r requirements.txt

3. Choose Launch Method:
   
   A) Desktop Launcher (Non-Technical Users)
      └─> Windows: Double-click Launch-DRE-Monitor.bat
      └─> Mac/Linux: ./launch-dre-monitor.sh
      └─> Dashboard opens at http://localhost:5173
      └─> Terminal shows live monitoring
   
   B) Command Line (Technical Users)
      └─> cd guardian
      └─> python cli.py monitor --dashboard
      └─> Dashboard opens at http://localhost:5173

4. Initial State
   └─> Monitor shows demo project (validation-test-2026)
   └─> Dashboard displays 3 views:
       • Leadership (strategic overview)
       • HALT (gate failure details)
       • Assertions (individual monitoring)
```

---

## Flow 2: Creating Your First Governance Project

```
1. Initialize Project
   └─> cd guardian
   └─> python cli.py init my-financial-model
   
2. Project Structure Created
   my-financial-model/
   ├── project_space/
   │   └── manifest.json       ← Define what to monitor
   ├── shared/                 ← Shared resources
   ├── logs/                   ← Audit history
   ├── config/                 ← Configuration
   └── README.md               ← Documentation

3. Configure Manifest
   └─> Edit project_space/manifest.json:
   
   {
     "project_id": "my-financial-model-001",
     "target_file": "Q1_forecast.xlsx",
     "assertions": [
       {
         "id": "ast-001",
         "logical_name": "revenue_forecast",
         "owner_role": "CFO",
         "binding": {"cell": "B10"},
         "distribution": {
           "min": 1000000,    ← Pessimistic case
           "mode": 1200000,   ← Most likely
           "max": 1500000     ← Optimistic case
         }
       }
     ]
   }

4. Add Excel File
   └─> Create project_space/Q1_forecast.xlsx
   └─> Add data to cell B10

5. Validate Configuration
   └─> python ../guardian/cli.py validate project_space/manifest.json
   └─> ✓ Manifest valid
   └─> ✓ PERT distributions valid
   └─> ✓ Cell bindings correct

6. Start Monitoring
   └─> python ../guardian/cli.py monitor --dashboard
   └─> System begins watching Q1_forecast.xlsx
```

---

## Flow 3: Daily Monitoring Workflow

```
User's Typical Day:

09:00 - Start Monitoring
   └─> Double-click Launch-DRE-Monitor.bat
   └─> Dashboard opens showing current state
   └─> Status: ● PASS (all assertions healthy)

10:30 - Update Excel Model
   └─> Open project_space/financial_model.xlsx
   └─> Change revenue forecast in B10: 1,200,000 → 1,650,000
   └─> Save file (Ctrl+S)
   
10:30:01 - Automatic Detection
   └─> File watcher detects change (0.9s debounce)
   └─> Governance cycle runs
   └─> Gate 2 (Stability) triggers HALT
   └─> Reason: 37.5% drift (threshold: 15%)
   
10:30:02 - UI Updates
   Terminal:
   ┌─────────────────────────────────────┐
   │ Status: ● HALT                      │
   │ Checks: 14    HALTs: 1              │
   │                                     │
   │ Assertion: revenue_forecast         │
   │   G1: P...  (Freshness PASS)        │
   │   G2: HA..  (Stability HALT)        │
   │   G4: S...  (Structure SKIP)        │
   └─────────────────────────────────────┘
   
   Dashboard:
   - Leadership View: Shows HALT badge
   - "View HALT Details" button appears
   
10:31 - User Investigates
   └─> Click "View HALT Details" in dashboard
   └─> See gate failure breakdown:
       • Gate: Stability (G2)
       • Status: HALT
       • Drift: 37.5% (threshold: 15%)
       • Current: 1,650,000
       • Baseline: 1,200,000
       • Reason: "Drift exceeds stability threshold"

10:32 - User Decision Point

   Option A: Data Error - Fix the Data
      └─> Correct Excel value to 1,300,000
      └─> Save file
      └─> Auto-detection triggers new cycle
      └─> Status: ● PASS ✓
   
   Option B: Valid Change - Update PERT Range
      └─> Edit manifest.json
      └─> Update distribution: max: 1500000 → 2000000
      └─> Restart monitor
      └─> Status: ● PASS ✓
   
   Option C: Temporary Override - Bypass HALT
      └─> Click "Bypass HALT" in dashboard
      └─> Enter justification: "Board approved new target"
      └─> Submit override
      └─> System continues in PASS mode
      └─> Override logged to audit_log.jsonl

12:00 - Review Activity
   └─> python cli.py audit --limit 20
   └─> See history:
       • 10:30:01 - HALT - revenue_forecast (37.5% drift)
       • 10:32:15 - OVERRIDE - User bypassed (justified)
       • 09:00:00 - CYCLE - All gates passed
```

---

## Flow 4: Multi-User Team Workflow

```
Team Structure:
- CFO (owns revenue assertions)
- VP Engineering (owns cost assertions)
- VP Sales (owns market assumptions)

Scenario: Conflicting Assumptions

Day 1 - CFO Updates Revenue
   └─> Updates revenue_forecast: min=1M, mode=1.2M, max=1.5M
   └─> Status: ● PASS

Day 2 - VP Sales Updates Market Share
   └─> Updates market_capture: min=5%, mode=8%, max=15%
   └─> Status: ● PASS
   └─> But... overlap integral with revenue is now 0.02 (below threshold)

Day 3 - Dashboard Alerts
   Leadership View:
   ┌──────────────────────────────────────────┐
   │ Departmental Alignment                   │
   │                                          │
   │ ⚠ Conflict Detected                      │
   │   revenue_forecast (CFO)                 │
   │   ↔ market_capture (VP Sales)            │
   │   Overlap: 2% (threshold: 5%)            │
   │                                          │
   │ Action Required: Reconcile assumptions   │
   └──────────────────────────────────────────┘

Day 4 - Team Meeting
   └─> CFO and VP Sales meet
   └─> Discuss assumptions
   └─> Agree on aligned ranges
   └─> Update both manifests
   └─> Conflict resolved ✓
```

---

## Flow 5: CI/CD Integration

```
Developer Workflow:

1. Local Development
   └─> Edit financial model
   └─> Run local check:
       python cli.py check manifest.json model.xlsx
   └─> ✓ All gates passed

2. Commit Changes
   └─> git add model.xlsx manifest.json
   └─> git commit -m "Update Q2 forecast"
   
3. Pre-commit Hook Runs
   #!/bin/bash
   cd guardian
   python cli.py check ../project_space/manifest.json ../project_space/*.xlsx
   
   └─> If HALT: Commit blocked
   └─> If PASS: Commit proceeds

4. Push to GitHub
   └─> git push origin main

5. GitHub Actions Runs
   
   .github/workflows/governance-check.yml:
   
   name: DRE Governance Check
   on: [push, pull_request]
   jobs:
     governance:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v2
         - uses: actions/setup-python@v2
         - run: pip install -r requirements.txt
         - run: |
             cd guardian
             python cli.py check \
               ../project_space/manifest.json \
               ../project_space/financial_model.xlsx
   
6. CI Results
   └─> ✓ PASS: PR can be merged
   └─> ✗ HALT: PR blocked, requires review

7. Audit Trail
   └─> All checks logged to audit_log.jsonl
   └─> Queryable: python cli.py audit --since 2026-01-20
```

---

## Flow 6: System Health Monitoring

```
Admin Workflow:

Daily Health Check:
   └─> python cli.py doctor
   
   Output:
   ┌──────────────────────────────────────────┐
   │ System Diagnostics                       │
   │                                          │
   │ ✓ Python Version: 3.11.5 (OK)            │
   │ ✓ openpyxl: installed                    │
   │ ✓ scipy: installed                       │
   │ ✓ numpy: installed                       │
   │ ✓ pydantic: installed                    │
   │ ✓ fastapi: installed                     │
   │ ✓ watchdog: installed                    │
   │ ✓ rich: installed                        │
   │ ✓ File Permissions: OK                   │
   │ ✓ API Server: Reachable                  │
   │                                          │
   │ Overall Status: HEALTHY ✓                │
   └──────────────────────────────────────────┘

Weekly Audit Review:
   └─> python cli.py audit --filter override --limit 100
   └─> Identify patterns:
       • Frequent overrides? → PERT ranges too tight
       • Same user bypassing? → Review authorization
       • Specific assertion? → Investigate root cause

Monthly Governance Report:
   └─> python cli.py audit --since 2026-01-01 > monthly_report.json
   └─> Analyze:
       • Total cycles run
       • HALT frequency
       • Override justifications
       • Gate failure patterns
```

---

## Flow 7: Troubleshooting Common Issues

```
Issue 1: Monitor Keeps Reloading
   Problem: File watcher triggering on audit log writes
   Solution: ✓ FIXED - audit_log.jsonl now excluded
   
Issue 2: Dashboard Empty
   Problem: Monitor not running with --dashboard flag
   Solution:
   └─> Restart: python cli.py monitor --dashboard
   └─> Check: http://localhost:5173
   └─> Verify port 8000 not blocked

Issue 3: Excel Changes Not Detected
   Problem: File name mismatch
   Solution:
   └─> Check manifest.json "target_file" field
   └─> Ensure exact match with Excel filename
   └─> Try: python cli.py validate manifest.json

Issue 4: Persistent HALT State
   Problem: Data outside PERT range
   Solution:
   └─> Open dashboard → View HALT Details
   └─> See drift percentage
   └─> Either:
       A) Fix data to be within range
       B) Update PERT distribution in manifest
       C) Bypass with justification

Issue 5: Import Errors
   Problem: Missing dependencies
   Solution:
   └─> Run: python cli.py doctor
   └─> Install missing: pip install -r requirements.txt
   └─> Verify: python --version (should be 3.11+)
```

---

## Summary: User Interaction Points

### Non-Technical User
- Double-click `Launch-DRE-Monitor.bat`
- View dashboard at http://localhost:5173
- Edit Excel files normally
- Click "Bypass HALT" when needed
- Press Ctrl+C to stop

### Technical User
- Run: `python cli.py monitor --dashboard`
- Run: `python cli.py check manifest.json model.xlsx`
- Run: `python cli.py audit --limit 20`
- Edit manifest.json for configuration
- Integrate with CI/CD

### Administrator
- Run: `python cli.py doctor` (health checks)
- Run: `python cli.py init project-name` (create projects)
- Review audit logs regularly
- Configure PERT ranges
- Manage team access

### Developer
- Edit `guardian/core/brain.py` (gate logic)
- Edit `dashboard/src/` (UI components)
- Run tests: `python test_*.py`
- Read `FRICTION_LOG.md` for known issues
- Follow architecture in `docs/`
