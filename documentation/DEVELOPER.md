# DRE Engine - Developer Documentation

This file has been moved to the documentation folder for better organization.

If you are reading this, you are already in the right place!

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
┌──────────────────────────────────────────────┐
│        CLI Interface (cli.py)       │ ← User commands
├──────────────────────────────────────────────┤
│      Monitor (monitor.py)           │ ← Orchestration
├──────────────────────────────────────────────┤
│   Core Engine (brain.py)            │ ← Gate logic
├──────────────────────────────────────────────┤
│   Data Layer (ingestor.py)          │ ← Excel I/O
├──────────────────────────────────────────────┤
│   API Bridge (bridge.py)            │ ← Web API
└──────────────────────────────────────────────┘
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
└── documentation/DEVELOPER.md
