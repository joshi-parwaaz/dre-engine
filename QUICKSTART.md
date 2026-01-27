# DRE Guardian - Quick Start Guide

## For New Users (Installing from GitHub)

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url> dre-guardian
cd dre-guardian

# Install Python dependencies
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Create Your First Project

```bash
cd guardian
python cli.py init my-first-project
cd my-first-project
```

This creates:
- `project_space/` - Where your Excel files and manifest live
- `project_space/manifest.json` - Configuration defining what to monitor
- `README.md` - Project-specific documentation

### 3. Configure Your Manifest

Edit `project_space/manifest.json`:

```json
{
  "project_id": "my-first-project-001",
  "target_file": "financial_model.xlsx",
  "assertions": [
    {
      "id": "ast-001",
      "logical_name": "revenue_forecast",
      "owner_role": "finance",
      "binding": {"cell": "B10"},
      "distribution": {
        "min": 1000000,
        "mode": 1200000,
        "max": 1500000
      }
    }
  ]
}
```

### 4. Create Your Excel File

Create `project_space/financial_model.xlsx` with your data.
The cell `B10` should contain the revenue forecast value.

### 5. Run Your First Audit

**One-time check:**
```bash
python ../guardian/cli.py check project_space/manifest.json project_space/financial_model.xlsx
```

**Live monitoring:**
```bash
python ../guardian/cli.py monitor
```

**Live monitoring with web dashboard:**
```bash
python ../guardian/cli.py monitor --dashboard
```

Then open: http://localhost:5173

### 6. Desktop Launcher (Windows)

Double-click `Launch-DRE-Monitor.bat` to start the monitor directly from desktop.

---

## Common Workflows

### Check System Health
```bash
python cli.py doctor
```

### View Audit History
```bash
python cli.py audit --limit 10
```

### Validate Manifest
```bash
python cli.py validate project_space/manifest.json
```

### View Configuration
```bash
python cli.py config
```

---

## Production Deployment

### Option 1: Command Line Tool
Install as system-wide command:
```bash
pip install -e .
dre monitor --dashboard
```

### Option 2: Desktop Application
Use the provided launcher scripts:
- Windows: `Launch-DRE-Monitor.bat`
- Linux/Mac: `launch-dre-monitor.sh`

### Option 3: Background Service
Run as daemon (Linux):
```bash
python cli.py watch start --daemon
```

---

## Understanding the Output

### Monitor View
```
Status: ● HALT    - System detected drift outside acceptable range
Status: ● PASS    - All assertions within bounds

Gate Status:
  P... = PASS      - Gate approved
  HA.. = HALT      - Gate blocked (drift/staleness/conflict)
  S... = SKIPPED   - Not applicable
```

### Web Dashboard

**Leadership View** - High-level strategic monitoring:
- Data Health Status (assertion quality)
- Departmental Alignment (conflict detection)
- Governance Velocity (audit timeline)

**HALT View** - Detailed gate failure analysis:
- Which gates failed and why
- Drift percentages and thresholds
- Current vs baseline values

**Assertions View** - Individual assertion details:
- PERT distributions
- Gate status per assertion
- Ownership and SLA tracking

---

## Troubleshooting

**Monitor not detecting changes?**
- Make sure you're editing the correct Excel file
- Check file path in manifest matches actual file
- Run `dre doctor` to check file permissions

**Dashboard shows nothing?**
- Ensure monitor is running with `--dashboard` flag
- Check http://localhost:5173 is accessible
- Verify port 8000 isn't blocked

**"HALT" status - what does it mean?**
- Your data drifted outside expected PERT distribution
- Check the HALT view in dashboard for details
- Review gate_details to see drift percentage
- Either update your data or recalibrate the PERT distribution

---

## Next Steps

1. Read `docs/ARCHITECTURE.md` for system design
2. Explore audit logs: `python cli.py audit`
3. Customize manifest for your use case
4. Set up CI/CD integration with `dre check`
