# DRE Guardian - Installation & Usage Guide

## 🚀 For New Users (Production Setup)

### Quick Install (3 Steps)

1. **Get the code**
   ```bash
   git clone <your-repo-url> dre-guardian
   cd dre-guardian
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start monitoring**
   - **Windows**: Double-click `Launch-DRE-Monitor.bat`
   - **Linux/Mac**: Run `./launch-dre-monitor.sh`
   - **Command line**: `cd guardian && python cli.py monitor --dashboard`

That's it! Dashboard opens at http://localhost:5173

---

## 📖 First-Time User Workflow

### Create Your First Project

```bash
cd guardian
python cli.py init my-financial-model
cd my-financial-model
```

This creates:
```
my-financial-model/
  ├── project_space/
  │   └── manifest.json          # Define what to monitor
  ├── README.md                   # Project documentation
  └── .gitignore
```

### Configure What to Monitor

Edit `project_space/manifest.json`:

```json
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
        "min": 1000000,
        "mode": 1200000,
        "max": 1500000
      }
    }
  ]
}
```

### Add Your Excel File

Create `project_space/Q1_forecast.xlsx` with your data model.

### Run Governance Check

**One-time audit:**
```bash
python ../guardian/cli.py check project_space/manifest.json project_space/Q1_forecast.xlsx
```

**Live monitoring:**
```bash
python ../guardian/cli.py monitor --dashboard
```

**View history:**
```bash
python ../guardian/cli.py audit --limit 20
```

---

## 🖥️ Desktop Usage (Non-Technical Users)

### Windows
1. Double-click `Launch-DRE-Monitor.bat`
2. Terminal opens showing live monitoring
3. Web dashboard auto-opens at http://localhost:5173
4. Edit your Excel file - changes are detected automatically
5. Press `Ctrl+C` in terminal to stop

### Mac/Linux
1. Right-click `launch-dre-monitor.sh` → "Open With" → Terminal
2. Or from command line: `./launch-dre-monitor.sh`
3. Dashboard opens at http://localhost:5173
4. Press `Ctrl+C` to stop

---

## 📊 Understanding the Interface

### Terminal Monitor (CLI)
```
Status: ● HALT     - Data drifted outside bounds
Status: ● PASS     - Everything within range

Gate Status Codes:
  P... = PASS      - Approved
  HA.. = HALT      - Blocked (see dashboard for details)
  S... = SKIPPED   - Not applicable
```

### Web Dashboard

**Leadership View** (Strategic Overview):
- **Data Health Status**: How many assertions are healthy/warning/critical
- **Departmental Alignment**: Conflict detection between teams
- **Governance Velocity**: 24-hour timeline of checks/HALTs/overrides

**HALT View** (Troubleshooting):
- Which specific gates failed
- Drift percentage (how far data moved from expected range)
- Current vs baseline values
- Bypass option for authorized overrides

**Assertions View** (Details):
- Individual assertion status
- PERT distribution curves
- Ownership and SLA tracking

---

## 🛠️ Common Tasks

### Check System Health
```bash
python cli.py doctor
```

### View Recent Audit Logs
```bash
python cli.py audit --limit 20
```

### Query Specific Events
```bash
python cli.py audit --filter halt --since 2026-01-20
```

### Validate Configuration
```bash
python cli.py validate project_space/manifest.json
```

### View Settings
```bash
python cli.py config
```

---

## 🔧 Production Deployment Options

### Option 1: Desktop Application (Simplest)
Use the launcher scripts - no setup needed:
- `Launch-DRE-Monitor.bat` (Windows)
- `launch-dre-monitor.sh` (Linux/Mac)

### Option 2: System Command
Install as global command:
```bash
pip install -e .
dre monitor --dashboard
```

### Option 3: CI/CD Integration
Run one-time checks in your pipeline:
```yaml
# .github/workflows/governance-check.yml
- name: Run DRE Governance Check
  run: |
    python guardian/cli.py check \
      project_space/manifest.json \
      project_space/model.xlsx
```

### Option 4: Background Service
Run as daemon (Linux):
```bash
python cli.py watch start --daemon
```

---

## ❓ Troubleshooting

**Q: Monitor not detecting my Excel file changes?**
- Ensure Excel file name matches `target_file` in manifest.json
- Save the file (Ctrl+S) - auto-save doesn't always trigger
- Run `python cli.py doctor` to check file permissions

**Q: Dashboard shows nothing?**
- Make sure monitor is running with `--dashboard` flag
- Check http://localhost:5173 in browser
- Verify port 8000 isn't blocked by firewall

**Q: What does "HALT" mean?**
- Your data changed beyond expected PERT distribution range
- Click "View HALT Details" in dashboard to see specifics
- Either fix the data or update the PERT range in manifest.json

**Q: How do I update expected ranges?**
- Edit `manifest.json` → Find the assertion
- Update `distribution.min`, `distribution.mode`, `distribution.max`
- Restart monitor

---

## 📚 Next Steps

1. Read [QUICKSTART.md](QUICKSTART.md) for detailed tutorials
2. Explore `docs/ARCHITECTURE.md` for system design
3. Customize manifest.json for your use case
4. Set up CI/CD integration for automated checks

---

## 🔗 Quick Reference

| Task | Command |
|------|---------|
| Create project | `python cli.py init <name>` |
| Start monitoring | `python cli.py monitor --dashboard` |
| One-time check | `python cli.py check <manifest> <excel>` |
| View logs | `python cli.py audit --limit 20` |
| System health | `python cli.py doctor` |
| Validate config | `python cli.py validate <manifest>` |
| Desktop launch | Double-click `Launch-DRE-Monitor.bat` |

---

## 💡 Philosophy

> "The math is often right, but the assumptions are often lies."

DRE Guardian monitors the **assumptions** in your financial models, not just the formulas. It tracks:
- **Freshness**: Is this data still valid?
- **Stability**: Has the data drifted beyond expected variance?
- **Alignment**: Are departments' assumptions in conflict?
- **Structure**: Did the formula change unexpectedly?

When assumptions break, the system **HALTS** - forcing conscious review before proceeding.
