# DRE Engine - Developer Documentation

Technical documentation for developers contributing to or maintaining the DRE Engine project.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Development Setup](#development-setup)
4. [Core Components](#core-components)
5. [Building](#building)
6. [Testing](#testing)
7. [Contributing](#contributing)

---

## Architecture Overview

### System Design

DRE Engine follows a layered architecture:

```
┌─────────────────────────────────────┐
│        CLI Interface (cli.py)       │ ← User commands
├─────────────────────────────────────┤
│      Monitor (monitor.py)           │ ← Orchestration
├─────────────────────────────────────┤
│   Core Engine (brain.py)            │ ← Gate logic
├─────────────────────────────────────┤
│   Data Layer (ingestor.py)          │ ← Excel I/O
├─────────────────────────────────────┤
│   API Bridge (bridge.py)            │ ← Web API
└─────────────────────────────────────┘
```

### Key Design Principles

1. **Separation of Concerns** - Each module has a single responsibility
2. **Immutable Audit Trail** - Append-only JSONL logs
3. **Zero Data Leakage** - Only distributions exposed via API, not raw values
4. **User-Owned Data** - Tool observes, never modifies Excel files
5. **Preflight Validation** - Fail fast with actionable errors

---

## Project Structure

```
dre-engine/
├── guardian/                   # Main package
│   ├── __init__.py
│   ├── cli.py                 # Click-based CLI
│   ├── main.py                # Entry point
│   ├── monitor.py             # TUI monitoring loop
│   │
│   ├── api/                   # Web API
│   │   ├── __init__.py
│   │   ├── bridge.py          # FastAPI server
│   │   └── audit_logger.py    # JSONL logger
│   │
│   ├── core/                  # Core logic
│   │   ├── __init__.py
│   │   ├── brain.py           # Gate engine
│   │   ├── config.py          # Path resolution
│   │   ├── ingestor.py        # Excel reader
│   │   ├── loader.py          # Manifest parser
│   │   ├── schema.py          # Pydantic models
│   │   └── validator.py       # Preflight checks
│   │
│   ├── tools/                 # Utilities
│   │   ├── __init__.py
│   │   └── verify_signature.py
│   │
│   └── watcher/               # File system watcher
│       ├── __init__.py
│       └── watcher.py
│
├── dashboard/                 # React frontend
│   ├── src/
│   │   ├── App.tsx           # Main component
│   │   ├── main.tsx          # Entry point
│   │   └── components/        # UI components
│   ├── dist/                 # Build output (served by API)
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
├── guardian.spec             # PyInstaller spec
├── requirements.txt          # Python dependencies
├── README.md
├── USER_GUIDE.md
└── DEVELOPER.md
```

---

## Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+ (for dashboard)
- Windows 10/11 (for executable builds)
- Visual Studio Code (recommended)

### Clone and Install

```bash
git clone <repository-url>
cd dre-engine

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install dashboard dependencies
cd dashboard
npm install
cd ..
```

### Run in Development Mode

```bash
# Activate virtual environment
.venv\Scripts\activate

# Run CLI directly
python guardian/cli.py

# Or use as module
python -m guardian.cli
```

### Build Dashboard

```bash
cd dashboard
npm run build
cd ..
```

This creates `dashboard/dist/` which is served by the FastAPI backend.

---

## Core Components

### 1. CLI (cli.py)

**Purpose:** Command-line interface and interactive shell

**Key Features:**
- Click framework for command parsing
- Interactive REPL with `while True` loop
- Preflight validation integration
- User-friendly error handling

**Commands:**
- `init` - Create project scaffolding
- `doctor` - Run validation
- `monitor` - Start monitoring
- `dashboard` - Start with web UI (shortcut for `monitor --dashboard`)
- `check` - Run full 4-gate analysis (CI/CD compatible)
- `logs` - View audit trail
- `audit` - Query audit logs with filters
- `validate` - Check manifest schema
- `config` - Show/modify configuration
- `status` - Check system health
- `archive` - Archive old audit logs
- `verify` - Verify digital signatures

**Interactive Shell:**
```python
def interactive_shell():
    """Keeps process alive until 'exit' command"""
    while True:
        user_input = input("dre> ").strip()
        if user_input in ['exit', 'quit']:
            break
        # Parse and execute command
```

---

### 2. Monitor (monitor.py)

**Purpose:** Orchestrates file watching and governance cycles

**Key Components:**

**DREMonitor Class:**
- Initializes config, manifest, brain, audit logger
- Starts file watcher (watchdog)
- Runs governance cycles on file changes
- Manages bypass state
- Renders TUI with rich.Live

**Governance Cycle:**
```python
def run_governance_cycle(self):
    # 1. Read Excel data
    data = self.ingestor.read_data()
    
    # 2. Evaluate all gates
    results = self.brain.evaluate_all_gates(data)
    
    # 3. Log events
    if halt_detected:
        self.audit_logger.log_event("HALT", ...)
    
    # 4. Update dashboard state
    self.push_to_dashboard(results)
```

---

### 3. Brain (brain.py)

**Purpose:** Gate evaluation engine

**Four Gates:**

**Gate 1 - Freshness:**
```python
def evaluate_freshness(self, assertion):
    age_days = (now - last_updated).days
    if age_days > sla_days:
        return "HALT"
    return "PASS"
```

**Gate 2 - Stability:**
```python
def evaluate_stability(self, current_value, distribution):
    # PERT distribution PDF
    pdf_current = pert_pdf(current_value, min, mode, max)
    pdf_baseline = pert_pdf(baseline, min, mode, max)
    
    ratio = pdf_current / pdf_baseline
    if ratio < threshold:
        return "HALT"  # Unexpected volatility
    return "PASS"
```

**Gate 3 - Collision:**
```python
def evaluate_collision(self, assertion1, assertion2):
    # Calculate PERT overlap integral
    overlap = integrate(
        lambda x: min(pdf1(x), pdf2(x)),
        bounds
    )
    
    if overlap < cutoff:
        return "HALT"  # Conflicting changes
    return "PASS"
```

**Gate 4 - Alignment:**
```python
def evaluate_alignment(self, current_hash, baseline_hash):
    if current_hash != baseline_hash:
        return "HALT"  # Formula changed
    return "PASS"
```

---

### 4. Ingestor (ingestor.py)

**Purpose:** Excel file reading with retry logic

**Key Features:**
- Dual-pass reading (values + formulas)
- Exponential backoff for file locks
- Sheet and cell validation
- Formula hash calculation

**Read Flow:**
```python
def read_data(self, retries=5):
    for i in range(retries):
        try:
            wb_data = openpyxl.load_workbook(file, data_only=True)
            wb_logic = openpyxl.load_workbook(file, data_only=False)
            
            for assertion in assertions:
                sheet = wb_data[assertion.binding.sheet]
                value = sheet[assertion.binding.cell].value
                formula = wb_logic[...].value
                hash = sha256(formula).hexdigest()
                
                results[assertion.id] = {
                    "value": value,
                    "formula_hash": hash
                }
            
            return results
        except PermissionError:
            time.sleep(delay * (2 ** i))
    
    raise PermissionError("File locked after retries")
```

---

### 5. Validator (validator.py)

**Purpose:** Preflight validation before monitoring starts

**Validation Checks:**
1. Manifest file exists
2. JSON syntax is valid
3. Required fields present
4. Excel file exists
5. Excel file is readable
6. All referenced sheets exist
7. All referenced cells are valid
8. Cell values match expected types

**Error vs Warning:**
- **Errors** - Block monitoring (manifest syntax, missing file)
- **Warnings** - Allow monitoring (empty cells, type mismatches)

**Usage:**
```python
errors, warnings = PreflightValidator.validate_project(manifest_path)

if errors:
    print("Cannot start - fix these issues:")
    for error in errors:
        print(f"  {error.title}: {error.message}")
        print(f"  Fix: {error.fix}")
    sys.exit(1)
```

---

### 6. API Bridge (bridge.py)

**Purpose:** FastAPI server for web dashboard

**Endpoints:**

**WebSocket:**
```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Push-only architecture
    # Brain broadcasts state updates
```

**Override:**
```python
@app.post("/override")
async def submit_override(request: OverrideRequest):
    # Forward to monitor instance
    monitor_instance.register_bypass(
        assertion_ids=request.assertion_ids,
        justification=request.justification,
        ...
    )
```

**Audit:**
```python
@app.get("/api/audit/recent")
async def get_recent_audit(limit=50):
    # Read JSONL, filter last 24hrs
    events = parse_audit_log()
    recent = filter_by_timestamp(events, 24h)
    return paginate(recent, limit)
```

**Static Files:**
```python
# Serve React build
app.mount("/assets", StaticFiles(directory="dashboard/dist/assets"))

@app.get("/{full_path:path}")
async def serve_spa():
    return FileResponse("dashboard/dist/index.html")
```

---

### 7. Config (config.py)

**Purpose:** Path resolution for frozen/script modes

**PyInstaller Detection:**
```python
if getattr(sys, 'frozen', False):
    # Running as .exe
    bundle_dir = Path(sys._MEIPASS)  # Temp extraction
    app_dir = Path(sys.executable).parent  # Exe location
else:
    # Running as script
    bundle_dir = Path(__file__).parent.parent
    app_dir = bundle_dir.parent
```

**Path Resolution:**
```python
self.project_space = self.app_dir / "project_space"
self.manifest_path = self.project_space / "manifest.json"
self.audit_log_path = self.project_space / "audit_log.jsonl"
self.logs_dir = self.project_space / "logs"
```

**Lazy Directory Creation:**
```python
def ensure_project_space(self):
    """Create only when needed (not on startup)"""
    self.project_space.mkdir(parents=True, exist_ok=True)
```

---

## Building

### Build Executable with PyInstaller

```bash
# Clean build
pyinstaller guardian.spec --clean
```

**Output:** `dist/DREEngine.exe`

### guardian.spec Configuration

```python
a = Analysis(
    ['guardian/cli.py'],
    pathex=[],
    binaries=[],
    datas=[('dashboard/dist', 'dashboard/dist')],  # Bundle React app
    hiddenimports=['pydantic', 'fastapi', ...],
    ...
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DREEngine',
    onefile=True,  # Single-file executable
    console=True,  # Terminal-based
    ...
)
```

### Dashboard Build

```bash
cd dashboard
npm run build
```

Creates `dashboard/dist/` with:
- `index.html`
- `assets/*.js`
- `assets/*.css`

These files are bundled into the executable via `datas` in guardian.spec.

---

## Testing

### Manual Testing Workflow

1. **Create test project:**
   ```bash
   python guardian/cli.py
   > init
   ```

2. **Prepare test Excel file:**
   - Create simple .xlsx with sheets/cells matching manifest
   - Place in `project_space/`

3. **Validate:**
   ```bash
   > doctor
   ```

4. **Test monitoring:**
   ```bash
   > monitor --dashboard
   ```

5. **Trigger gates:**
   - Modify Excel values
   - Save file
   - Observe dashboard for HALT conditions

### Unit Test Structure (Future)

```python
# tests/test_brain.py
def test_freshness_gate():
    assertion = create_test_assertion(sla_days=7)
    assertion.last_updated = now - timedelta(days=8)
    
    result = brain.evaluate_freshness(assertion)
    assert result == "HALT"

# tests/test_validator.py
def test_missing_sheet():
    manifest = create_test_manifest(sheet="NonExistent")
    errors, _ = PreflightValidator.validate_project(manifest)
    
    assert len(errors) == 1
    assert "not found" in errors[0].message
```

---

## Contributing

### Code Style

- **Python:** PEP 8, type hints encouraged
- **TypeScript:** ESLint + Prettier
- **Naming:** Descriptive variable names, avoid abbreviations
- **Comments:** Explain *why*, not *what*

### Commit Message Format

```
<type>: <description>

[optional body]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `refactor` - Code restructuring
- `test` - Add/update tests
- `build` - Build system changes

**Example:**
```
feat: add preflight validation to monitor command

Prevents monitor from starting if manifest has errors.
Validates Excel file, sheets, and cell references before
initiating file watcher. Provides actionable error messages.
```

### Pull Request Process

1. Create feature branch: `git checkout -b feat/your-feature`
2. Make changes with descriptive commits
3. Test thoroughly (manual + automated if available)
4. Update documentation (README, USER_GUIDE as needed)
5. Submit PR with description of changes
6. Address review feedback
7. Squash and merge once approved

### Adding New Commands

1. **Define in cli.py:**
   ```python
   @cli.command()
   @click.option('--flag', is_flag=True)
   def newcommand(flag):
       """Description for help text"""
       print_banner()
       # Implementation
   ```

2. **Update banner:**
   ```python
   Quick Start:
     newcommand  Description
   ```

3. **Document:**
   - Add to README.md command table
   - Add section in USER_GUIDE.md
   - Update help text

### Adding New Gates

1. **Implement in brain.py:**
   ```python
   def evaluate_gate_5(self, assertion, data):
       """New validation logic"""
       if violation_detected:
           return {
               "status": "HALT",
               "reason": "...",
               "details": {...}
           }
       return {"status": "PASS"}
   ```

2. **Integrate in evaluate_all_gates:**
   ```python
   gate_5_result = self.evaluate_gate_5(assertion, data)
   ```

3. **Add narrative:**
   ```python
   def get_human_narrative(self, gate, details, name):
       if gate == "gate_5":
           return {
               "title": "...",
               "message": "...",
               "action": "..."
           }
   ```

4. **Update schema if needed:**
   ```python
   class GateStatus(BaseModel):
       gate_5: str
   ```

5. **Document behavior in USER_GUIDE.md**

---

## Troubleshooting Development Issues

### PyInstaller Fails

**Symptom:** Missing module errors in built .exe

**Solution:** Add to `hiddenimports` in guardian.spec:
```python
hiddenimports=[
    'pydantic',
    'your.missing.module',
    ...
]
```

### Dashboard Not Loading

**Symptom:** 404 on dashboard assets

**Solution:**
1. Rebuild dashboard: `cd dashboard && npm run build`
2. Verify `dashboard/dist/` exists
3. Check `datas` in guardian.spec includes dashboard/dist

### File Lock Issues

**Symptom:** "Excel file is locked" errors

**Solution:**
- Close Excel before testing
- Increase retry count in `ingestor.py`
- Check antivirus isn't locking files

---

## Performance Considerations

### Excel Read Performance

- Uses `read_only=True` for efficiency
- Dual-pass required (data + formulas)
- Large files (>10MB) may take 2-3 seconds

### Live TUI Refresh

- Refresh rate: 0.5 Hz (2 seconds)
- Only updates on state change
- Minimal CPU usage when idle

### Dashboard WebSocket

- Push-only architecture (no polling)
- Broadcasts only on governance events
- Minimal network overhead

---

## Security Considerations

### Data Privacy

- **Zero Leakage:** API exposes distributions, not raw values
- **Local Only:** API binds to 127.0.0.1 (no external access)
- **No Telemetry:** No data sent to external servers

### Audit Integrity

- **Append-Only:** Audit log cannot be modified in-place
- **Timestamped:** All events have UTC timestamps
- **Signed Overrides:** SHA-256 hash for non-repudiation

### File System Access

- **Read-Only Excel:** Never modifies user's Excel files
- **Project Space Only:** All writes confined to project_space/
- **No Elevation:** Runs with user permissions

---

## Deployment

### Distribution Checklist

- [ ] Build dashboard: `cd dashboard && npm run build`
- [ ] Clean build executable: `pyinstaller guardian.spec --clean`
- [ ] Test executable on clean Windows machine
- [ ] Verify all commands work
- [ ] Test doctor validation
- [ ] Test monitor with real Excel file
- [ ] Test dashboard loads correctly
- [ ] Package with README.md and USER_GUIDE.md
- [ ] Create zip archive for distribution

### Release Package Structure

```
DRE-Engine-v1.0.zip
├── DREEngine.exe
├── README.md
├── USER_GUIDE.md
└── examples/
    ├── sample-manifest.json
    └── sample-model.xlsx
```

---

## API Reference

### Manifest Schema (Pydantic)

```python
class DREManifest(BaseModel):
    project_id: str
    project_name: str
    target_file: str
    governance_config: GovernanceConfig
    assertions: List[Assertion]

class Assertion(BaseModel):
    id: str
    logical_name: str
    description: str
    owner_role: str
    last_updated: str
    sla_days: int
    binding: CellBinding
    baseline_value: float
    distribution: PERTDistribution

class CellBinding(BaseModel):
    cell: str
    sheet: str

class PERTDistribution(BaseModel):
    min: float
    mode: float
    max: float
```

### FastAPI Endpoints

**GET /health**
- Returns: `{"status": "active", "connections": int, "timestamp": str}`

**GET /api/governance/state**
- Returns: Current governance state (assertions, gate status, conflicts)

**POST /override**
- Body: `{assertion_ids: str[], justification: str, signature: str, timestamp: str, signature_hash: str}`
- Returns: `{status: "accepted"|"rejected", message: str, timestamp: str}`

**GET /api/audit/recent**
- Query: `?limit=50&offset=0`
- Returns: `{events: Event[], total: int, limit: int, offset: int}`

**GET /api/audit/summary**
- Returns: Aggregated metrics (total_events, by_severity, halt_count, etc.)

**WS /ws**
- WebSocket connection for real-time governance state pushes

---

## License

Proprietary - All Rights Reserved

---

## Contact

For development questions or contribution inquiries, contact the project maintainer.
