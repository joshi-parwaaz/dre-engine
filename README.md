# DRE Engine - Data Reliability Engine

**Epistemic Governance for Strategic Models**

DRE Engine is a specialized governance tool for Excel-based financial and strategic models. It monitors cell values in real-time, validates changes against statistical distributions, and enforces data integrity policies—ensuring that critical business decisions are based on reliable data.

---

## Features

- **📊 Real-time Monitoring** - Watches Excel files for changes and validates them instantly
- **🔒 Data Integrity Gates** - Four-gate validation system (Freshness, Stability, Collision, Alignment)
- **📈 Statistical Analysis** - PERT distribution modeling for epistemic uncertainty
- **🎯 Cell-level Governance** - Define assertions for specific cells and validation rules
- **🌐 Web Dashboard** - Visual interface with PERT curves, collision maps, and audit logs
- **📝 Immutable Audit Trail** - JSONL append-only ledger for full traceability
- **⚡ File Watcher** - Auto-triggers validation on Excel save events

---

## Quick Start

### Prerequisites

- Windows 10/11 (64-bit)
- Excel file (.xlsx format)
- Your existing strategic model

### Installation

1. **Download** `DREEngine.exe` from the releases page
2. **Place** the executable in a dedicated folder (e.g., `C:\DRE`)
3. **Run** the executable - a terminal window will open

### First-Time Setup

```
dre> init
```

This creates:
- `project_space/` - Directory for your files
- `manifest.json` - Configuration template

### Configure Your Project

1. **Place your Excel file** in `project_space/`
2. **Edit `manifest.json`:**
   - Set `target_file` to your Excel filename
   - Define assertions for cells you want to monitor
   - Configure governance thresholds

Example assertion:
```json
{
  "id": "revenue-forecast",
  "logical_name": "q1_revenue",
  "description": "Q1 2026 Revenue Forecast",
  "owner_role": "VP of Sales",
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

### Validate Configuration

```
dre> doctor
```

This checks:
- ✓ Manifest syntax is valid
- ✓ Excel file exists and is accessible
- ✓ Referenced sheets and cells exist
- ✓ Cell values match expected types

### Start Monitoring

```
dre> monitor
```

Or with web dashboard:
```
dre> monitor --dashboard
```

**You'll see:**
```
✓ Monitoring started
Watching: your-model.xlsx
Dashboard: http://127.0.0.1:8000
Press Ctrl+C to stop monitoring
```

The tool now watches your Excel file. Any changes will be validated in real-time.

---

## Commands

| Command | Description |
|---------|-------------|
| `init` | Create project scaffolding |
| `doctor` | Validate project readiness |
| `monitor` | Start governance tracking |
| `dashboard` | Start with web UI (shortcut for `monitor --dashboard`) |
| `check` | Run full 4-gate analysis (CI/CD compatible) |
| `logs` | Tail audit logs in terminal |
| `audit` | Query audit logs with filters |
| `validate` | Validate manifest schema |
| `config` | Show or modify configuration |
| `status` | Check system health |
| `archive` | Archive old audit logs |
| `verify` | Verify digital signatures |
| `exit` | Close the application |
| `help` | Show all commands |

---

## Governance Gates

DRE Engine uses a four-gate validation system:

### Gate 1: Freshness
Ensures data isn't stale based on defined SLA periods.

### Gate 2: Stability
Detects unexpected volatility using PERT distribution analysis.

### Gate 3: Collision
Identifies conflicting changes across dependent assertions.

### Gate 4: Alignment
Validates formula integrity to prevent calculation hijacking.

**When a gate triggers HALT:**
- Monitoring continues but flags the issue
- Audit log records the event
- Dashboard shows human-friendly narrative
- Authorized users can submit bypass requests

---

## Dashboard

Access the web dashboard at `http://127.0.0.1:8000` when monitoring with `--dashboard` flag.

**Features:**
- **Galaxy View** - Visual representation of all assertions
- **PERT Curves** - Statistical distribution overlays
- **Collision Map** - Conflict detection between assertions
- **Audit Log** - Timestamped governance events
- **Bypass Form** - Submit override requests with justification

---

## File Structure

```
DREEngine.exe
project_space/
  ├── your-model.xlsx          # Your Excel file (you provide)
  ├── manifest.json            # Governance configuration
  ├── audit_log.jsonl          # Immutable event ledger
  ├── logs/
  │   └── dre.log             # Application logs
  └── archives/                # Compressed historical logs
```

---

## Manifest Configuration


### Required Fields

```json
{
  "project_id": "unique-identifier",
  "target_file": "your-model.xlsx",
  "stability_threshold": 0.15,
  "overlap_integral_cutoff": 0.05,
  "assertions": [...]
}
```

### Assertion Structure

Each assertion monitors a specific cell:

```json
{
  "id": "unique-assertion-id",
  "logical_name": "variable_name",
  "owner_role": "Responsible person/role",
  "last_updated": "2026-02-01T10:30:00Z",
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

---

## Troubleshooting

### "Excel file is locked"
**Problem:** The Excel file is open in Excel.  
**Solution:** Close the file and try again.

### "Sheet 'X' not found"
**Problem:** Sheet name in manifest doesn't match Excel.  
**Solution:** Check exact sheet name (case-sensitive) and update manifest.

### "Manifest contains invalid JSON"
**Problem:** Syntax error in manifest.json.  
**Solution:** Use a JSON validator or text editor with syntax checking.

### Monitor won't start
**Problem:** Validation errors blocking startup.  
**Solution:** Run `doctor` to see detailed error messages and fix instructions.

---

## Best Practices

1. **Run `doctor` before `monitor`** - Catch configuration errors early
2. **Use descriptive assertion IDs** - Makes audit logs easier to understand
3. **Set realistic distributions** - Based on historical data patterns
4. **Review audit logs regularly** - Track governance health over time
5. **Close Excel before monitoring** - Prevents file lock issues
6. **Define clear SLAs** - Align freshness checks with update cadence

---

## Support

For issues, questions, or feedback, please contact your system administrator or refer to the USER_GUIDE.md for detailed documentation.

---

## Technical Details

- **Platform:** Windows 64-bit
- **Excel Format:** .xlsx (Office Open XML)
- **Python Version:** 3.11+
- **Key Dependencies:** openpyxl, scipy, numpy, fastapi, rich
- **License:** Proprietary

---

## Version

**DRE Engine v1.0.1**  
Production Release - February 2026
