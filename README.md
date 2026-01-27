# DRE Engine: Data Reliability & Epistemic Governance

> **"The math is often right, but the assumptions are often lies."**

The **DRE Engine (Data Reliability Engine)** is an ambient governance layer designed to prevent systemic failure in high-stakes strategic modeling. It functions as a "Silent Guardian" over volatile Excel environments, enforcing a hardened reality through mathematical gates and human accountability.

---

## 🚀 Quick Start for New Users

**Want to use this tool right away?**

1. **Install**: `pip install -r requirements.txt`
2. **Launch**: Double-click `Launch-DRE-Monitor.bat` (Windows) or run `./launch-dre-monitor.sh` (Mac/Linux)
3. **Dashboard**: Opens at http://localhost:5173

📖 **First-time setup?** → See [INSTALL.md](INSTALL.md) for complete guide  
📚 **Learn by doing?** → See [QUICKSTART.md](QUICKSTART.md) for tutorials

---

## ⚖️ The Three Epistemic Principles

The engine enforces three non-negotiable laws derived from the **Governance Manifesto**:

1. **The Principle of Attribution (Gate 0):** No data exists without a human anchor. Every governed cell must be mapped to an `owner_role`.
2. **The Principle of Decay (Gate 1):** Information has a half-life. Data that exceeds its Service Level Agreement (SLA) triggers a systemic **HALT**.
3. **The Principle of Uncertainty (Gate 2):** Point estimates are rejected. All inputs are treated as PERT distributions to expose departmental conflicts via the **Overlap Integral**.

---

## 🏗️ Architecture: The Guardian Triad

The DRE Engine operates as a local-first, zero-leakage sidecar to your existing workflow.

### 1. The Watcher (`guardian/watcher/`)
An OS-level daemon that monitors `.xlsx` files.
- **Debounce Logic:** 0.9s delay to ensure file stability before ingestion.
- **Mutex Control:** Prevents race conditions during heavy write cycles.

### 2. The Brain (`guardian/core/`)
The analytical engine that processes the **Manifest Contract**.
- **Gate 1: Freshness** - Linear Temporal Decay (SLA enforcement).
- **Gate 2: Stability** - PERT Distribution Overlap (drift detection).
- **Gate 3: Convergence** - Rate of change monitoring.
- **Gate 4: Structure** - SHA-256 Formula Hijack detection.

### 3. The Bridge & UI (`guardian/api/` & `dashboard/`)
The interface for the "Human-in-the-Loop."
- **WebSockets:** Instant state-push to the dashboard on every save.
- **Visual Evidence:** Real-time PERT curve rendering for conflict identification.
- **Auditable Override:** Captures signed justifications for every governance bypass.

**Core Design Principles:**
- **The Brain refuses silently; the UI explains loudly**
- **Zero-Leakage** - UI receives only distributions, never raw values
- **Push, not Poll** - WebSocket pushes state when HALTs occur
- **Visual math ≠ Governance math** - React approximates, Python computes truth

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Excel or compatible spreadsheet software

### 1. Backend Setup (Guardian)

```bash
# From dre-engine/
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r guardian/requirements.txt

# Start the Guardian (API + Watcher)
cd guardian
python start.py
```

**Guardian starts:**
- API Server on `http://127.0.0.1:8000`
- File Watcher monitoring `project_space/`
- WebSocket endpoint at `ws://127.0.0.1:8000/ws`

### 2. Frontend Setup (Dashboard)

```bash
# In a new terminal, from dre-engine/
cd dashboard
npm install
npm run dev
```

```bash
# In a new terminal, from dre-engine/
cd dashboard
npm install
npm run dev
```

**Dashboard opens at:** `http://localhost:5173`

### 3. Initialize Your First Project

Use the DRE CLI to scaffold a new governed project:

```bash
# From dre-engine/
python guardian/cli.py init my-project --path project_space
cd project_space/my-project
```

This creates:
- `manifest.json` - Governance contract template
- Project structure with proper directories
- `.gitignore` and README

### 4. Test the System

1. Edit `manifest.json` to define your assertions
2. Create an Excel file matching the manifest bindings
3. Save changes to the Excel file
4. **Guardian detects changes** → Runs 4 Gates → Pushes to UI on HALT
5. Browser auto-opens with visual PERT distributions and override form

---

## 🛠️ CLI Toolchain (`guardian/cli.py`)

The `dre` command-line utility provides DevOps and scaffolding capabilities.

| Command | Function | Exit Code |
| :--- | :--- | :---: |
| `dre init <project>` | Scaffolds project structure and generates `manifest.json` | - |
| `dre validate <manifest>` | Pre-flight check for manifest schema and PERT sanity | 0/1 |
| `dre check <manifest> <excel>` | One-shot 4-gate analysis for CI/CD | 0=PASS, 1=HALT |
| `dre watch start\|stop` | Controls the ambient file-monitoring daemon | - |
| `dre audit [--filter]` | Queries the audit logs for historical overrides | - |
| Command | Function | Exit Code |
| :--- | :--- | :---: |
| `dre init <project>` | Scaffolds project structure and generates `manifest.json` | - |
| `dre validate <manifest>` | Pre-flight check for manifest schema and PERT sanity | 0/1 |
| `dre check <manifest> <excel>` | One-shot 4-gate analysis for CI/CD | 0=PASS, 1=HALT |
| `dre watch start\|stop` | Controls the ambient file-monitoring daemon | - |
| `dre audit [filters]` | Queries Active Ledger with severity/type/date filters | - |
| `dre archive` | Compresses old logs to Cold Storage, clears active ledger | - |
| `dre status` | Health check for API server and watcher daemon | - |

**Usage Examples:**

```bash
# Initialize project
python guardian/cli.py init financial-model --path .

# Validate manifest schema
python guardian/cli.py validate project_space/manifest.json

# Run governance check (CI/CD integration)
python guardian/cli.py check manifest.json data.xlsx --json

# Check system health
python guardian/cli.py status

# Query audit logs (Active Ledger)
python guardian/cli.py audit --severity critical --since 2026-01-01 --limit 100

# Archive old audit logs (Cold Storage)
python guardian/cli.py archive --older-than 365 --compress
```

**CRITICAL CONSTRAINT:** The CLI imports and reuses the **same** core modules as the Guardian runtime. No alternative logic paths. No reimplementation of gates. This ensures behavioral consistency across interactive and automated workflows.

---

## 📊 The 4-Gate Analysis System

| Gate | Purpose | Authority | Implementation |
|------|---------|-----------|----------------|
| **Gate 1: Freshness** | Temporal decay (SLA enforcement) | Principle of Decay | `brain.gate_1_freshness()` |
| **Gate 2: Stability** | Distribution overlap (drift detection) | Principle of Uncertainty | `brain.gate_2_stability()` |
| **Gate 3: Convergence** | Rate of change monitoring | Principle of Stability | `brain.gate_3_convergence()` |
| **Gate 4: Structure** | Formula hijack detection | Principle of Integrity | `brain.gate_4_structure()` |

**Gate Status Values:**
- `PASS` - Assertion within acceptable parameters
- `HALT` - Governance violation detected, action required
- `SKIP` - Insufficient data to evaluate (e.g., no baseline value)

---

## 🔄 Data Flow Architecture

```
Excel Save
    ↓
Watcher (Debounced)
    ↓
Ingestor (Read Data + Formulas)
    ↓
Brain (4-Gate Analysis)
    ↓
HALT Detected?
    ↓
Bridge (WebSocket Push)
    ↓
Dashboard (Visual Evidence)
    ↓
Human Decision (Override Request)
    ↓
Audit Log (Guilt Recording)
```

**On HALT:**
1. Browser auto-opens at `http://localhost:5173`
2. WebSocket pushes Zero-Leakage payload (distributions only)
3. React renders PERT curves and overlap analysis
4. User reviews visual evidence
5. Override request submitted (records justification + signature)
6. **Brain remains the authority** - override doesn't auto-clear HALT---

## 📋 Three-Tiered Audit Model

The DRE Engine implements a professional audit architecture that prevents unreasonable data volume while ensuring compliance and forensic capability.

### 1️⃣ Hot Window (Dashboard)
**Scope:** Last 24 hours or current model session  
**Purpose:** Real-time diagnostics for active work  
**Implementation:** `/api/audit/recent` endpoint with pagination (limit 50 default)

**What it shows:**
- Summary card with severity breakdown (CRITICAL/WARN/INFO)
- Recent events with filtering by severity
- HALT count and override count for current session
- Auto-refresh every 10 seconds

**Use Case:** Lead analyst asks *"What changed since I last opened this sheet?"*

### 2️⃣ Active Ledger (CLI)
**Scope:** Current reporting period (e.g., this fiscal quarter)  
**Purpose:** Compliance verification and forensic analysis  
**Implementation:** `dre audit` command with advanced filters

**Query Examples:**
```bash
# Show all critical events from last month
dre audit --severity critical --since 2026-01-01 --limit 100

# Find all manual overrides by specific user
dre audit --filter override --limit 200

# Review all HALTs from the last week
dre audit --filter halt --severity critical --since 2026-01-19
```

**Use Case:** Compliance officer verifies integrity of a specific model version.

### 3️⃣ Cold Storage (Archive)
**Scope:** Historical records older than 1 year  
**Purpose:** Long-term legal protection and data governance  
**Implementation:** `dre archive` command with automatic compression

**Archive Process:**
```bash
# Archive logs older than 180 days with compression
dre archive --older-than 180 --compress

# Output:
# ✓ Archived: 3,421 events
# ✓ Remaining: 892 events
# ✓ Location: archives/audit_archive_20250101_20250715.jsonl.gz
# ✓ Compression: 78.3% reduction
```

**Features:**
- Automatic date-range detection
- Gzip compression (configurable)
- Active log cleared to maintain performance
- Preserved in `project_space/archives/` folder

**Use Case:** Legal team retrieves 3-year-old audit trail for regulatory investigation.

---

### Audit Event Structure

```json
{
  "timestamp": "2026-01-26T12:34:56Z",
  "session_id": "20260126-12",
  "severity": "CRITICAL",
  "event_type": "HALT",
  "assertion_id": "ast-001",
  "user_anchor": "CFO",
  "details": {
    "gate_1_freshness": {"status": "PASS", "age_hours": 2.3},
    "gate_2_stability": {"status": "HALT", "overlap_integral": 0.23},
    "gate_4_structure": {"status": "PASS"}
  }
}
```

**Severity Levels:**
- **INFO:** Routine operations, validation passes, formula checks
- **WARN:** Manual overrides, stability warnings, non-critical issues
- **CRITICAL:** HALT events, security breaches, data corruption

**Session Tracking:**  
The `session_id` groups events by 24-hour windows (e.g., `20260126-12` = Jan 26, 2026, 12:00 UTC hour). This enables:
- "Show me everything from yesterday's session"
- Correlation of related events across the day
- Performance isolation for dashboard queries

---

## 🔒 Zero-Leakage Payload

The UI receives **only** distribution shapes, never raw values or baselines. This enforces information compartmentalization.

**Example Payload:**

```json
{
  "project_id": "strategic-forecast-2026",
  "timestamp": "2026-01-22T14:30:00Z",
  "assertions": [
    {
      "id": "ast-001",
      "logical_name": "market_capture_rate",
      "owner_role": "sales",
      "gate_status": {
        "freshness": "PASS",
        "stability": "HALT",
        "convergence": "PASS",
        "structure": "PASS"
      },
      "distribution": {
        "min": 0.05,
        "mode": 0.12,
        "max": 0.15
      }
    },
    {
      "id": "ast-002",
      "logical_name": "development_cost",
      "owner_role": "engineering",
      "gate_status": {
        "freshness": "PASS",
        "stability": "HALT",
        "convergence": "PASS",
        "structure": "PASS"
      },
      "distribution": {
        "min": 500000,
        "mode": 750000,
        "max": 1000000
      }
    }
  ],
  "conflict_pairs": [["sales", "engineering"]],
  "halt_reason": "Gate 2 (Stability) violation: Distribution drift exceeds threshold"
}
```

**No raw values. No baselines. No sensitive operational data.**

---

## 📁 Project Structure

```
dre-engine/
├── guardian/              # Python Backend (The Brain)
│   ├── core/              # Gate Engine, Loader, Ingestor, Schema
│   │   ├── __init__.py
│   │   ├── brain.py       # 4-Gate Analysis Engine
│   │   ├── loader.py      # Manifest loader and validator
│   │   ├── ingestor.py    # Excel reader with lock handling
│   │   └── schema.py      # Pydantic models (DREManifest, Assertion)
│   ├── watcher/           # File System Monitor
│   │   ├── __init__.py
│   │   └── watcher.py     # OS-level file change detection
│   ├── api/               # FastAPI Bridge (WebSocket)
│   │   ├── __init__.py
│   │   ├── bridge.py      # API server + WebSocket broadcaster
│   │   └── audit_logger.py # Override request persistence
│   ├── cli.py             # Command-line toolchain
│   ├── main.py            # Governance cycle orchestration
│   ├── start.py           # Startup script (API + Watcher)
│   └── requirements.txt   # Python dependencies
│
├── dashboard/             # React Frontend (The UI)
│   ├── src/
│   │   ├── App.tsx        # Main app with WebSocket listener
│   │   ├── components/
│   │   │   ├── Galaxy.tsx          # WebGL starfield background
│   │   │   ├── PertOverlapChart.tsx # PERT distribution visualization
│   │   │   └── OverrideForm.tsx     # Override request form
│   │   ├── main.tsx
│   │   └── index.css      # Glass morphism design system
│   ├── package.json
│   └── vite.config.ts
│
├── project_space/         # Governed Projects (Excel + Manifests)
├── shared/                # Shared resources and configs
├── logs/                  # Audit logs
└── README.md              # This file
```

---

## 🧪 Manifest Contract Schema

The `manifest.json` file is the governance contract that defines all assertions.

**Example:**

```json
{
  "project_id": "financial-forecast-2026-q1",
  "target_file": "forecast_model.xlsx",
  "stability_threshold": 0.15,
  "overlap_integral_cutoff": 0.05,
  "assertions": [
    {
      "id": "ast-001",
      "logical_name": "revenue_forecast",
      "owner_role": "finance",
      "last_updated": "2026-01-22T10:00:00Z",
      "sla_days": 1,
      "binding": {
        "cell": "B10",
        "formula_hash": "sha256:4a3f2e..."
      },
      "baseline_value": 1200000,
      "distribution": {
        "min": 1000000,
        "mode": 1200000,
        "max": 1500000
      }
    }
  ]
}
```

**Key Fields:**
- `id` - Stable UUID for the assertion
- `logical_name` - Human-readable identifier
- `owner_role` - The human anchor (Principle of Attribution)
- `last_updated` - Timestamp for decay calculation (Principle of Decay)
- `sla_days` - Maximum age before HALT
- `binding.cell` - Excel cell reference
- `binding.formula_hash` - SHA-256 of the formula for hijack detection
- `distribution` - PERT parameters (min/mode/max)

---

## ⚙️ Override Behavior

**CRITICAL:** The Override Form does NOT:
- Clear HALTs
- Touch the Brain
- Grant permission
- Modify data

**It ONLY records guilt.**

The Brain evaluates override requests against policy rules. The override system exists to:
1. Capture human justification
2. Create an audit trail
3. Attribute accountability
4. Enable post-mortem analysis

**Override Request Schema:**

```json
{
  "timestamp": "2026-01-22T14:35:00Z",
  "assertion_id": "ast-001",
  "requested_by": "john.doe@company.com",
  "justification": "Sales pipeline data delayed due to CRM outage",
  "signature": "John Doe",
  "status": "PENDING"
}
```

---

## 📚 Backtesting & Case Studies

The DRE Engine has been validated against historical failures to quantify intervention value.

- **[Lehman Brothers (2008)](./docs/cases/lehman.md):** Detecting liquidity decay and stale housing recovery assumptions via Gate 1 (Freshness).
- **[Boeing 737 MAX](./docs/cases/boeing.md):** Identifying the alignment breach between software logic and sensor reliability via Gate 2 (Stability).
- **[NASA Mars Orbiter](./docs/cases/nasa.md):** Catching structural shocks in unit conversion logic via Gate 4 (Structure) formula hashing.

*Note: Case study documentation is under development.*

---

## 🔐 Security Posture

- **Local-First:** No strategic data ever leaves the local machine.
- **Read-Only Ingestion:** Guardian never locks or modifies the source Excel file.
- **Zero-Leakage:** API server is bound strictly to `127.0.0.1` (localhost only).
- **Audit Trail:** All override requests logged with timestamp, user, and justification.
- **No External Dependencies:** All computation happens locally using scipy/numpy.

**Network Configuration:**
- API Server: `127.0.0.1:8000` (localhost binding only)
- Dashboard: `localhost:5173` (dev server)
- WebSocket: `ws://127.0.0.1:8000/ws` (localhost only)

---

## 🧑‍💻 Development

### Running Tests

```bash
cd guardian
python -m pytest tests/ -v
```

### Module Structure

All modules are properly packaged with `__init__.py`:
- `guardian/`
- `guardian/core/`
- `guardian/watcher/`
- `guardian/api/`

**Import Example:**

```python
from guardian.core.loader import ManifestLoader
from guardian.core.brain import GateEngine
from guardian.core.ingestor import ExcelIngestor
```

### Execution Context

Run from `dre-engine/` or `dre-engine/guardian/`:
- From `dre-engine/`: `python guardian/start.py`
- From `guardian/`: `python start.py`

### Tech Stack

**Backend:**
- Python 3.11
- FastAPI 0.128.0 (API framework)
- uvicorn 0.40.0 (ASGI server)
- scipy 1.17.0 (Beta distribution calculations)
- numpy 2.4.1 (Numerical operations)
- openpyxl 3.1.5 (Excel file reading)
- watchdog 6.0.0 (File system monitoring)
- pydantic 2.12.5 (Schema validation)
- click 8.1.7 (CLI framework)
- rich 13.7.0 (Terminal formatting)

**Frontend:**
- React 18.3.1
- TypeScript 5.6.2
- Vite 6.0.3 (Build tool)
- recharts 2.15.0 (Chart library)
- OGL (WebGL library for Galaxy background)

---

## 📖 Documentation

- [Governance Manifesto](./docs/manifesto.md) - Epistemic principles and design philosophy
- [API Reference](./docs/api.md) - WebSocket protocol and REST endpoints
- [CLI Guide](./docs/cli.md) - Complete command reference
- [Manifest Schema](./docs/schema.md) - Contract specification
- [Backtesting Guide](./docs/backtesting.md) - Historical validation methodology

*Note: Extended documentation is under development.*

---

## 🤝 Contributing

This is a private research project. Internal contributions only.

**Development Guidelines:**
1. Never modify the Brain's gate logic via the CLI (reuse only)
2. All UI state must be derived from WebSocket pushes (no polling)
3. Never leak raw values to the frontend (distributions only)
4. All override requests must be logged with full attribution

---

## 📄 License

Internal use only. Proprietary.

---

© 2026 DRE-Engine | Epistemic Governance for Strategic Intelligence
