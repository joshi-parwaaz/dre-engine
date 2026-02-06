# DRE Engine - User Guide

Complete guide for using the Data Reliability Engine to govern your strategic Excel models.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Project Initialization](#project-initialization)
4. [Configuration](#configuration)
5. [Validation](#validation)
6. [Monitoring](#monitoring)
7. [Dashboard Usage](#dashboard-usage)
8. [Audit Trail](#audit-trail)
9. [Bypass Workflow](#bypass-workflow)
10. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is DRE Engine?

DRE Engine is a governance tool that monitors your Excel-based financial and strategic models. It ensures that critical cells contain reliable data by:

- Validating changes against statistical distributions
- Detecting unexpected volatility
- Enforcing data freshness policies
- Preventing formula tampering
- Logging all governance events

### Who is it for?

- **Data Analysts** - Working with strategic Excel models
- **Finance Teams** - Managing forecasts and budgets
- **Business Leaders** - Making decisions based on model outputs
- **Compliance Officers** - Requiring audit trails for data changes

### Key Concepts

- **Assertion** - A rule that governs a specific Excel cell
- **Gate** - A validation check (Freshness, Stability, Collision, Alignment)
- **HALT** - When a gate detects a policy violation
- **Bypass** - Authorized override of a HALT condition
- **Audit Log** - Immutable record of all governance events

---

## Installation

### System Requirements

- Windows 10 or 11 (64-bit)
- Minimum 4GB RAM
- 500MB free disk space
- Excel file in .xlsx format

### Installation Steps

1. **Download** `DREEngine.exe` from your administrator
2. **Create a folder** for DRE Engine (e.g., `C:\DRE`)
3. **Move the executable** into this folder
4. **Double-click** `DREEngine.exe` to launch

**First Launch:**
```
╔══════════════════════════════════════════════════╗
║                                                  ║
║   DRE ENGINE - Data Reliability Engine          ║
║   Epistemic Governance for Strategic Models     ║
║                                                  ║
╚══════════════════════════════════════════════════╝

Quick Start:
  init        Create project scaffolding
  doctor      Validate project readiness
  monitor     Start governance tracking
  dashboard   Start with web UI
  check       Run 4-gate analysis

Welcome! Type 'init' to get started, or 'help' for all commands.

dre>
```

The terminal stays open and waits for your commands.

---

## Project Initialization

### Create Project Structure

```
dre> init
```

**What happens:**
1. Creates `project_space/` directory next to the executable
2. Generates `manifest.json` template inside it
3. Shows success message with next steps

**Output:**
```
⚡ Initializing DRE Project

Location: C:\DRE\project_space

→ Creating manifest.json template...
  ✓ Created: manifest.json

✓ Project structure created

Required next steps:
  1. Place your Excel file in: C:\DRE\project_space
  2. Edit manifest.json:
     • Set target_file to your Excel filename
     • Define assertions for cells you want to monitor
     • Update project metadata
  3. Run monitor to start governance tracking
```

### Place Your Excel File

**Important:** DRE Engine does NOT create or modify your Excel file. You must provide it.

1. **Copy** your existing Excel model to `project_space/`
2. **Note the exact filename** (e.g., `Q1-Forecast.xlsx`)
3. Keep the file **closed** (not open in Excel)

---

## Configuration

### Edit manifest.json

Open `project_space/manifest.json` in a text editor (Notepad, VS Code, etc.)

### Basic Configuration


```json
{
  "project_id": "q1-2026-forecast",
  "target_file": "Q1-Forecast.xlsx",
  "stability_threshold": 0.15,
  "overlap_integral_cutoff": 0.05,
  "assertions": [...]
}
```

**Fields:**
- `project_id` - Unique identifier (no spaces, use hyphens)
- `target_file` - **Exact** filename of your Excel file
- `stability_threshold` - (optional) Default: 0.15
- `overlap_integral_cutoff` - (optional) Default: 0.05

### Define Assertions

Each assertion monitors one cell. Example:


```json
{
  "id": "revenue-forecast",
  "logical_name": "q1_revenue",
  "owner_role": "VP of Sales",
  "last_updated": "2026-02-01T10:00:00Z",
  "sla_days": 7,
  "binding": {
    "cell": "B2",
    "sheet": "Dashboard"
  },
  "baseline_value": 1000000.0,
  "distribution": {
    "min": 850000.0,
    "mode": 1000000.0,
    "max": 1200000.0
  }
}
```

**Assertion Fields:**

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique identifier | `"revenue-forecast"` |
| `logical_name` | Variable name | `"q1_revenue"` |
| `description` | What this cell represents | `"Q1 Revenue Forecast"` |
| `owner_role` | Who maintains this value | `"VP of Sales"` |
| `last_updated` | ISO timestamp | `"2026-02-01T10:00:00Z"` |
| `sla_days` | Max age before stale | `7` |
| `binding.sheet` | Excel sheet name | `"Dashboard"` |
| `binding.cell` | Cell reference | `"B2"` |
| `baseline_value` | Expected value | `1000000.0` |
| `distribution.min` | Pessimistic bound | `850000.0` |
| `distribution.mode` | Most likely value | `1000000.0` |
| `distribution.max` | Optimistic bound | `1200000.0` |

**PERT Distribution Guide:**

The min/mode/max values define the expected range:
- **min** - Worst-case scenario
- **mode** - Most likely outcome (peak of distribution)
- **max** - Best-case scenario

Example for revenue:
- min: $850K (economic downturn)
- mode: $1M (baseline plan)
- max: $1.2M (aggressive growth)

### Multiple Assertions

Add multiple assertions to monitor different cells:

```json
"assertions": [
  {
    "id": "revenue-forecast",
    "logical_name": "q1_revenue",
    ...
  },
  {
    "id": "cost-estimate",
    "logical_name": "q1_costs",
    ...
  },
  {
    "id": "profit-margin",
    "logical_name": "margin",
    ...
  }
]
```

---

## Validation

### Pre-Flight Check

Before monitoring, validate your configuration:

```
dre> doctor
```

**What it checks:**
1. Manifest file exists and has valid JSON
2. Required fields are present
3. Excel file exists at specified path
4. All referenced sheets exist
5. All referenced cells are valid
6. Cell values match expected types

**Successful Output:**
```
🔬 Preflight Validation

Validating: C:\DRE\project_space\manifest.json

✓ READY TO MONITOR
All validation checks passed. You can run 'monitor' to start governance tracking.
```

**Error Output Example:**
```
✗ Blocking Issues Found

Issue 1: Sheet 'Dashboard' not found

Assertion 'revenue-forecast' refers to sheet 'Dashboard',
but that sheet does not exist in your Excel file.

Available sheets: 'Sheet1', 'Summary', 'Data'

Fix:
  • Open your Excel file and check the exact sheet name (case-sensitive)
  • Update the 'sheet' field in assertion 'revenue-forecast' to match

✗ NOT READY - Fix 1 issue before running monitor
```

**Fix errors and run `doctor` again** until you see "✓ READY TO MONITOR".

---

## Monitoring

### Start Basic Monitoring

```
dre> monitor
```

**Output:**
```
✓ Preflight validation passed

✓ Monitoring started
Watching: Q1-Forecast.xlsx
Press Ctrl+C to stop monitoring

[Live TUI Display]
```

The terminal shows a live dashboard with:
- Current status (PASS/HALT)
- Assertion states
- Total checks performed
- Recent audit events

### Start with Web Dashboard

```
dre> monitor --dashboard
```

**Additional output:**
```
✓ Monitoring started
Watching: Q1-Forecast.xlsx
Dashboard: http://127.0.0.1:8000
Press Ctrl+C to stop monitoring
```

The web dashboard opens automatically in your browser.

### What Happens During Monitoring

1. **Initial Check** - Reads all cells and validates them
2. **File Watching** - Monitors Excel file for save events
3. **Auto-Validation** - When you save Excel, gates re-evaluate
4. **Continuous** - Runs until you press Ctrl+C

### Stop Monitoring

Press **Ctrl+C** in the terminal:

```
Monitoring stopped
```

The process exits cleanly. No data is lost.

### Normal Workflow

1. Start monitoring: `monitor --dashboard`
2. Open your Excel file in Excel
3. Make changes
4. Save the file
5. DRE Engine validates changes automatically
6. Check dashboard for results
7. When done, press Ctrl+C to stop

---

## Dashboard Usage

### Access Dashboard

Open browser to: `http://127.0.0.1:8000`

### Dashboard Components

#### 1. Assertion Table
Shows all monitored cells with current status:
- Green checkmarks: All gates passed
- Red X: HALT condition detected
- Cell name, owner, and last update time

#### 2. PERT Overlap Chart
Visual comparison of current value against expected distribution:
- Blue curve: Expected distribution (min/mode/max)
- Red line: Current value
- Shaded area: Overlap integral (confidence)

#### 3. Conflict Collision Map
Shows assertions that may have conflicting changes:
- Dots represent assertions
- Lines connect conflicting pairs
- Color indicates severity

#### 4. Epistemic Health Map
Overall system health visualization:
- Gate status for each assertion
- Historical trend
- Aggregate metrics

#### 5. Audit Log
Recent governance events:
- Timestamp
- Event type (HALT, PASS, OVERRIDE)
- Assertion affected
- Severity level
- User/system actor

#### 6. Governance Velocity
Rate of changes and validation cycles over time.

### Interpreting HALT Conditions

When a gate triggers HALT, the dashboard shows:

**Title:** What happened (e.g., "🔔 Data Freshness Alert")

**Message:** Plain-English explanation of the issue

**Action:** What to do next

**Example:**
```
🔔 Data Freshness Alert

'Q1 Revenue Forecast' was last updated 8 days ago,
exceeding the 7-day SLA defined in the governance policy.

Action: Update the cell value or submit a bypass request
with justification if the current value remains valid.
```

---

## Audit Trail

### Audit Log Format

All events are logged to `project_space/audit_log.jsonl` (JSON Lines format).

Each line is a JSON event:
```json
{
  "timestamp": "2026-02-01T14:30:15.123456Z",
  "event_type": "HALT",
  "assertion_id": "revenue-forecast",
  "severity": "CRITICAL",
  "user_anchor": "SYSTEM",
  "details": {
    "gate": "freshness",
    "reason": "SLA exceeded: 8 days > 7 days"
  }
}
```

### Event Types

| Event Type | Description |
|------------|-------------|
| `INIT` | Monitoring started |
| `CHECK` | Routine validation cycle |
| `PASS` | All gates passed |
| `HALT` | Gate violation detected |
| `OVERRIDE_REQUEST` | Bypass submitted |
| `BYPASS_APPROVED` | Override accepted |
| `BYPASS_EXPIRED` | Temporary bypass ended |

### View Audit Logs

From CLI:
```
dre> logs
```

Or from dashboard: **Audit Log** section

---

## Bypass Workflow

### When to Use Bypass

If a HALT occurs but you've verified the change is intentional:
1. Understand why the gate triggered
2. Confirm the data is correct
3. Submit a bypass request with justification

### Submit Bypass (Dashboard)

1. Click **Override** button on halted assertion
2. Fill out the bypass form:
   - **Justification:** Detailed explanation
   - **Signature:** Your name/identifier
3. Click **Submit Override**

**Example Justification:**
```
Market conditions changed unexpectedly due to new competitor entry.
Revenue forecast adjusted down by 15% to reflect realistic outlook.
Approved by CFO in meeting 2026-02-01.
```

### Bypass Validation

The system checks:
- Assertion must be in HALT state
- Justification must be provided
- Signature must be present
- Bypass is time-limited (1 hour default)

**If accepted:**
```
✓ Bypass registered in Monitor authoritative state
```

The HALT is suppressed for 1 hour, allowing work to continue.

**If rejected:**
```
✗ Bypass rejected
Assertion 'revenue-forecast' is not in HALT state - cannot bypass
```

### Bypass Expiration

After the bypass expires:
- Gates re-evaluate automatically
- If issue persists, HALT triggers again
- Must submit new bypass if still needed

---

## Troubleshooting

### Common Issues

#### "Cannot Start Monitor"

**Symptom:** `✗ Cannot Start Monitor` with blocking issues listed

**Solution:** Run `doctor` to see detailed errors, fix each issue, then retry

---

#### "Excel file is locked"

**Symptom:** `Excel file is locked after 5 attempts`

**Cause:** File is open in Excel

**Solution:**
1. Save and close Excel
2. Wait 2 seconds
3. Run `monitor` again

---

#### "Sheet 'X' not found"

**Symptom:** Error mentioning missing sheet

**Cause:** Sheet name mismatch (case-sensitive)

**Solution:**
1. Open Excel
2. Note **exact** sheet name (check spelling, spaces, case)
3. Update `manifest.json` to match exactly
4. Run `doctor` to verify

---

#### "Manifest contains invalid JSON"

**Symptom:** JSON syntax error with line number

**Cause:** Missing comma, bracket, or quote

**Solution:**
1. Open `manifest.json` in a text editor
2. Check the line mentioned in error
3. Common mistakes:
   - Missing comma after values
   - Unmatched `{` or `[`
   - Unescaped quotes in strings
4. Use online JSON validator if needed
5. Save and run `doctor`

---

#### "Cell 'B2' is empty"

**Symptom:** Warning about empty cell

**Cause:** Referenced cell has no value

**Solution:**
- **If intentional:** Ignore warning (non-blocking)
- **If unintentional:** Check cell reference in manifest

---

#### Dashboard Won't Load

**Symptom:** Browser shows "Can't reach this page"

**Cause:** Monitor not running with `--dashboard` flag

**Solution:**
1. Stop monitoring (Ctrl+C)
2. Restart with: `monitor --dashboard`
3. Refresh browser

---

### Error Message Guide

| Error | Meaning | Fix |
|-------|---------|-----|
| "Manifest file not found" | No manifest.json | Run `init` first |
| "Excel file not found" | Wrong filename in manifest | Check `target_file` field |
| "Invalid cell reference" | Typo in cell coordinate | Use format like "A1", "B12" |
| "NOT READY" | Validation failed | Run `doctor` for details |
| "Monitoring blocked" | Pre-flight check failed | Fix issues shown, then retry |

---

### Getting Help

1. **Run `doctor`** - Shows detailed validation results
2. **Check audit log** - May reveal patterns
3. **Review manifest.json** - Ensure all fields are correct
4. **Contact administrator** - Provide error messages and logs

---

## Best Practices

### Configuration

- ✅ Use descriptive assertion IDs (`revenue-q1`, not `a1`)
- ✅ Set realistic PERT distributions based on historical data
- ✅ Define SLAs that match actual update frequency
- ✅ Document owner roles clearly

### Daily Usage

- ✅ Run `doctor` before starting work
- ✅ Close Excel before running `monitor`
- ✅ Monitor with dashboard for visibility
- ✅ Review audit log weekly
- ✅ Submit bypass requests with detailed justifications

### File Management

- ✅ Keep Excel file in `project_space/`
- ✅ Back up `manifest.json` regularly
- ✅ Archive old audit logs periodically
- ✅ Don't delete `audit_log.jsonl` (immutable record)

### Troubleshooting

- ✅ Always check `doctor` output first
- ✅ Read error messages completely
- ✅ Fix one issue at a time
- ✅ Test after each fix

---

## Appendix: Manifest Reference

### Complete Template


```json
{
  "project_id": "your-project-id",
  "target_file": "your-model.xlsx",
  "stability_threshold": 0.15,
  "overlap_integral_cutoff": 0.05,
  "assertions": [
    {
      "id": "example-assertion",
      "logical_name": "example_cell",
      "owner_role": "Role Name",
      "last_updated": "2026-02-01T10:00:00Z",
      "sla_days": 7,
      "binding": {
        "cell": "A1",
        "sheet": "Sheet1"
      },
      "baseline_value": 0.0,
      "distribution": {
        "min": 0.0,
        "mode": 0.0,
        "max": 0.0
      }
    }
  ]
}
```

### Field Constraints

- `project_id`: Alphanumeric, hyphens allowed, no spaces
- `sla_days`: Integer ≥ 1
- `binding.cell`: Valid Excel reference (A1, B12, AA100, etc.)
- `distribution.min` < `distribution.mode` < `distribution.max`
- `last_updated`: ISO 8601 format with timezone

---

## Version History

**v1.0** - February 2026
- Production release
- Four-gate validation system
- Web dashboard
- Immutable audit trail
- Bypass workflow
