# Changelog

All notable changes to the DRE Engine project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.0.1] - 2026-02-06

### Fixed
- **Monitor dashboard link** - Dashboard URL now displays prominently at monitor startup
- **Monitor refresh** - Changed from constant refresh to static display that only updates on state changes
- **Check command** - Fixed ExcelIngestor API integration for standalone governance checks

### Added
- `dashboard` command - Shortcut for `monitor --dashboard` to quickly launch web UI
- `check` command - Run full 4-gate governance analysis with CI/CD exit codes

### Improved
- Monitor TUI now uses static text output for better terminal compatibility
- Reduced CPU usage during monitoring (no unnecessary screen refreshes)

---

## [1.0.0] - 2026-02-01

### Initial Production Release

**Major Features:**
- ✅ Four-gate validation system (Freshness, Stability, Collision, Alignment)
- ✅ Real-time Excel file monitoring with auto-triggering
- ✅ Web dashboard with PERT curves and conflict visualization
- ✅ Immutable audit trail (JSONL format)
- ✅ Bypass workflow with justification and signatures
- ✅ Interactive CLI with persistent shell
- ✅ Comprehensive preflight validation

### CLI & UX

**Added:**
- Interactive REPL shell with command parsing
- `init` command - Creates project scaffolding (no mock data)
- `doctor` command - Preflight validation with actionable errors
- `monitor` command - Starts governance tracking
- `monitor --dashboard` - Launches with web UI
- Runtime status messaging ("Monitoring started", "Press Ctrl+C to stop")
- Clean exit handling (no error framing on Ctrl+C)
- Banner optimized for 80-character terminals
- Welcome message guiding users to run `init`

**Improved:**
- User-friendly error messages (no stack traces)
- Explicit data ownership model (users provide Excel files)
- Lazy directory creation (no empty folders on startup)
- Clear separation between blocking errors and warnings

### Core Engine

**Added:**
- Gate 1: Freshness validation with SLA enforcement
- Gate 2: Stability analysis using PERT distributions
- Gate 3: Collision detection via overlap integrals
- Gate 4: Formula alignment (hijack detection)
- Human-readable narrative generation for each gate
- Bypass request validation and expiration
- Active bypass state management

**Improved:**
- Exponential backoff for Excel file lock handling
- Dual-pass reading (values + formulas)
- Sheet and cell existence validation
- Type checking for cell values

### API & Dashboard

**Added:**
- FastAPI server with WebSocket push architecture
- Static file serving for React build
- `/api/governance/state` - Current governance snapshot
- `/api/audit/recent` - Filtered audit events (last 24 hours)
- `/api/audit/summary` - Aggregated metrics
- `/override` endpoint - Bypass request submission
- CORS middleware for localhost access
- Auto-open browser on dashboard start

**Dashboard Components:**
- Assertion table with real-time status
- PERT overlap chart with distribution visualization
- Conflict collision map
- Epistemic health map
- Live audit log viewer
- Bypass request form with validation
- Governance velocity metrics

### Validation

**Added:**
- `PreflightValidator` - Comprehensive project readiness checks
- Manifest JSON syntax validation
- Excel file existence and accessibility checks
- Sheet and cell reference validation
- Cell type matching verification
- Detailed error messages with fix instructions
- Warning system for non-blocking issues

**Checks:**
1. Manifest file exists
2. JSON syntax is valid
3. Required fields present
4. Excel file exists
5. Excel file is readable (not locked)
6. Referenced sheets exist
7. Referenced cells are valid
8. Cell values match expected types

### Configuration

**Added:**
- `Config` class with frozen/script mode detection
- Automatic path resolution (relative to executable)
- Lazy directory creation helpers
- Logging configuration with file handlers
- Dashboard directory path resolution

**Paths:**
- `project_space/` - User data directory (created on demand)
- `logs/` - Application logs (created when needed)
- `archives/` - Compressed audit logs
- `manifest.json` - Governance configuration
- `audit_log.jsonl` - Immutable event ledger

### File Watching

**Added:**
- Watchdog integration for file system monitoring
- Debouncing (0.9 seconds) to avoid duplicate triggers
- Auto-detection of Excel save events
- Observer lifecycle management

### Audit Logging

**Added:**
- JSONL append-only ledger
- Event types: INIT, CHECK, PASS, HALT, OVERRIDE_REQUEST, BYPASS_APPROVED
- Timestamped events (UTC)
- Severity levels: INFO, WARN, CRITICAL
- User/system actor tracking
- SHA-256 signature hashing for overrides

### Build System

**Added:**
- PyInstaller spec file for single-file executable
- Dashboard build integration (React → dist → bundled)
- Hidden import declarations for all dependencies
- Runtime hooks for pywintypes, pythoncom
- Console mode with interactive shell
- Icon embedding support

### Documentation

**Added:**
- README.md - Project overview and quick start
- USER_GUIDE.md - Complete user documentation
- DEVELOPER.md - Technical documentation for contributors
- CHANGELOG.md - Version history
- LICENSE - Proprietary license terms

### Dependencies

**Python:**
- click - CLI framework
- rich - Terminal UI and formatting
- openpyxl - Excel file reading
- scipy - PERT distribution calculations
- numpy - Statistical operations
- pydantic - Schema validation
- fastapi - Web API framework
- uvicorn - ASGI server
- watchdog - File system monitoring

**JavaScript:**
- React - UI framework
- TypeScript - Type safety
- Vite - Build tool
- Recharts - Chart library

### Known Issues

None at release.

### Breaking Changes

None (initial release).

---

## Release Notes Format

**[Version] - YYYY-MM-DD**

### Added
- New features

### Changed
- Updates to existing functionality

### Deprecated
- Features marked for removal

### Removed
- Deleted features

### Fixed
- Bug fixes

### Security
- Security vulnerability patches
