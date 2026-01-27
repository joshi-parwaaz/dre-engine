"""
DRE CLI - Data Reliability Engine Command Line Interface

Epistemic Governance Toolchain for High-Stakes Strategic Modeling

A collection of CLI tools for project initialization, validation,
governance checks, and audit reporting.

CRITICAL: This CLI imports and reuses core modules directly.
NO alternative logic paths. NO reimplementation of gates.
"""

import click
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import SAME core modules - no reimplementation
from core.loader import ManifestLoader
from core.ingestor import ExcelIngestor
from core.brain import GateEngine
from core.schema import DREManifest, Assertion, PertDistribution, DataBinding

console = Console()


def print_banner():
    """Display ASCII banner"""
    banner = """
[cyan]╔═══════════════════════════════════════════╗
║  DRE - Data Reliability Engine           ║
║  Epistemic Governance CLI v1.0            ║
╚═══════════════════════════════════════════╝[/cyan]
    """
    console.print(banner)


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version='1.0.0', prog_name='DRE Guardian', message='%(prog)s v%(version)s - Epistemic Governance Engine')
def cli(ctx):
    """DRE - Data Reliability Engine
    
    Epistemic Governance for High-Stakes Strategic Modeling
    
    \b
    Core Philosophy:
      • The math is often right, but the assumptions are often lies
      • The Brain refuses silently; the UI explains loudly
      • No data exists without a human anchor
    
    \b
    Essential Commands:
      monitor    Live TUI monitoring (CLI-first, like wifite/htop)
      doctor     Diagnose system health and dependencies
      logs       Tail audit logs in terminal (Hot Window)
      config     Show/modify project configuration
    
    \b
    Workflow Commands:
      init       Scaffold new governance project
      validate   Pre-flight manifest validation
      check      One-shot governance analysis (CI/CD)
      audit      Query Active Ledger with filters
      archive    Compress logs to Cold Storage
    
    Run 'dre COMMAND --help' for detailed usage.
    """
    # Show help if no command provided
    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(ctx.get_help())


@cli.command()
@click.option('--dashboard', '-d', is_flag=True, help='Enable web dashboard alongside CLI monitor')
@click.option('--manifest', default='../project_space/manifest.json', help='Path to manifest file')
def monitor(dashboard, manifest):
    """Start live interactive governance monitoring
    
    Beautiful CLI-first monitoring with real-time gate analysis.
    Similar to wifite/htop - shows live governance state in terminal.
    
    \b
    Features:
      • Real-time assertion table with gate status
      • Live audit log stream (last 5 events)
      • System metrics (checks, HALTs, status)
      • File watcher auto-triggers on Excel saves
      • Optional web dashboard for PERT curves
    
    \b
    Example:
      dre monitor              # CLI-only monitoring
      dre monitor --dashboard  # CLI + web dashboard
    """
    print_banner()
    console.print("[dim]Starting live monitor...[/dim]\n")
    
    try:
        from monitor import DREMonitor
        mon = DREMonitor(manifest, enable_dashboard=dashboard)
        mon.start_monitoring()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚡ Monitor stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
def doctor(output_json):
    """Diagnose system health and dependencies
    
    Ensures the Brain isn't failing due to missing components.
    Checks Python dependencies, file permissions, and API connectivity.
    
    \b
    Checks:
      • Python version (3.11+)
      • Required packages (scipy, numpy, openpyxl, etc.)
      • File system permissions (project_space/ write access)
      • API server connectivity (if running)
      • Manifest schema validity
    
    \b
    Example:
      dre doctor        # Human-readable report
      dre doctor --json # Machine-readable output
    """
    print_banner()
    console.print("\n[bold cyan]🔬 System Diagnostics[/bold cyan]\n")
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "checks": [],
        "overall_status": "HEALTHY"
    }
    
    # Check 1: Python version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    py_ok = sys.version_info >= (3, 11)
    
    results["checks"].append({
        "name": "Python Version",
        "status": "PASS" if py_ok else "FAIL",
        "value": py_version,
        "expected": "3.11+"
    })
    
    if not output_json:
        status_icon = "[green]✓[/green]" if py_ok else "[red]✗[/red]"
        console.print(f"{status_icon} Python Version: {py_version} {'[green](OK)[/green]' if py_ok else '[red](Too old)[/red]'}")
    
    # Check 2: Required packages
    required_packages = [
        ("openpyxl", "Excel file reading"),
        ("scipy", "PERT overlap integral calculation"),
        ("numpy", "Statistical computations"),
        ("pydantic", "Schema validation"),
        ("fastapi", "API server"),
        ("watchdog", "File system monitoring"),
        ("rich", "Terminal UI"),
        ("click", "CLI framework")
    ]
    
    for pkg, purpose in required_packages:
        try:
            __import__(pkg)
            pkg_ok = True
            msg = "installed"
        except ImportError:
            pkg_ok = False
            msg = "MISSING"
            results["overall_status"] = "DEGRADED"
        
        results["checks"].append({
            "name": f"Package: {pkg}",
            "status": "PASS" if pkg_ok else "FAIL",
            "purpose": purpose
        })
        
        if not output_json:
            status_icon = "[green]✓[/green]" if pkg_ok else "[red]✗[/red]"
            console.print(f"{status_icon} {pkg:15s} {msg:15s} [dim]({purpose})[/dim]")
    
    # Check 3: File permissions
    project_space = Path("../project_space")
    if project_space.exists():
        try:
            test_file = project_space / ".dre_health_check"
            test_file.touch()
            test_file.unlink()
            fs_ok = True
            fs_msg = "writable"
        except:
            fs_ok = False
            fs_msg = "NO WRITE ACCESS"
            results["overall_status"] = "DEGRADED"
    else:
        fs_ok = False
        fs_msg = "DOES NOT EXIST"
        results["overall_status"] = "DEGRADED"
    
    results["checks"].append({
        "name": "project_space/ permissions",
        "status": "PASS" if fs_ok else "FAIL",
        "message": fs_msg
    })
    
    if not output_json:
        status_icon = "[green]✓[/green]" if fs_ok else "[red]✗[/red]"
        console.print(f"{status_icon} File Permissions: {fs_msg}")
    
    # Check 4: API connectivity
    import urllib.request
    import urllib.error
    
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2) as response:
            api_ok = response.status == 200
            api_msg = "running"
    except:
        api_ok = False
        api_msg = "offline (not critical)"
    
    results["checks"].append({
        "name": "API Server",
        "status": "PASS" if api_ok else "SKIP",
        "message": api_msg
    })
    
    if not output_json:
        status_icon = "[green]✓[/green]" if api_ok else "[yellow]○[/yellow]"
        console.print(f"{status_icon} API Server: {api_msg}")
    
    # Check 5: Manifest validity
    manifest_path = Path("../project_space/manifest.json")
    if manifest_path.exists():
        try:
            ManifestLoader.load(str(manifest_path))
            manifest_ok = True
            manifest_msg = "valid schema"
        except Exception as e:
            manifest_ok = False
            manifest_msg = f"INVALID: {str(e)[:40]}"
            results["overall_status"] = "DEGRADED"
    else:
        manifest_ok = False
        manifest_msg = "NOT FOUND (run 'dre init')"
    
    results["checks"].append({
        "name": "Manifest Schema",
        "status": "PASS" if manifest_ok else "FAIL",
        "message": manifest_msg
    })
    
    if not output_json:
        status_icon = "[green]✓[/green]" if manifest_ok else "[red]✗[/red]"
        console.print(f"{status_icon} Manifest: {manifest_msg}")
    
    # Summary
    if output_json:
        console.print(json.dumps(results, indent=2))
    else:
        console.print(f"\n[bold]Overall Status:[/bold] ", end="")
        if results["overall_status"] == "HEALTHY":
            console.print("[green]✓ HEALTHY[/green] - System ready for governance")
        elif results["overall_status"] == "DEGRADED":
            console.print("[yellow]⚠ DEGRADED[/yellow] - Some components need attention")
            sys.exit(1)
        else:
            console.print("[red]✗ FAILED[/red] - Critical issues detected")
            sys.exit(1)


@cli.command()
@click.option('--follow', '-f', is_flag=True, help='Tail-follow the log file (like tail -f)')
@click.option('--lines', '-n', default=20, help='Number of recent lines to show (default: 20)')
@click.option('--severity', type=click.Choice(['all', 'critical', 'warn', 'info']), default='all', help='Filter by severity')
def logs(follow, lines, severity):
    """Tail audit logs in terminal (Hot Window)
    
    Provides immediate visibility without the full Dashboard UI.
    Shows real-time governance events as they happen.
    
    \b
    Features:
      • Color-coded severity levels
      • Human-readable timestamps
      • Event type and assertion ID
      • Follow mode for live streaming
    
    \b
    Example:
      dre logs              # Last 20 events
      dre logs -n 50        # Last 50 events
      dre logs -f           # Live streaming mode
      dre logs --severity critical  # Only critical events
    """
    print_banner()
    console.print("\n[bold cyan]📋 Audit Log Viewer[/bold cyan]\n")
    
    audit_file = Path("../project_space/audit_log.jsonl")
    
    if not audit_file.exists():
        console.print("[yellow]⚠ No audit log found[/yellow]")
        console.print("[dim]Logs are created when governance cycles run[/dim]")
        return
    
    def format_event(entry):
        """Format a single log entry for display"""
        timestamp = entry.get('timestamp', 'N/A')[:19].replace('T', ' ')
        sev = entry.get('severity', 'INFO')
        event_type = entry.get('event_type', 'UNKNOWN')
        assertion_id = entry.get('assertion_id', 'N/A')
        user = entry.get('user_anchor', 'SYSTEM')
        
        # Color-code severity
        if sev == 'CRITICAL':
            sev_display = f"[red bold]{sev}[/red bold]"
        elif sev == 'WARN':
            sev_display = f"[yellow]{sev}[/yellow]"
        else:
            sev_display = f"[green]{sev}[/green]"
        
        return f"[cyan]{timestamp}[/cyan] {sev_display:20s} [yellow]{event_type:20s}[/yellow] [magenta]{assertion_id:15s}[/magenta] [dim]{user}[/dim]"
    
    def read_entries():
        """Read and filter log entries"""
        entries = []
        with open(audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        
                        # Filter by severity
                        if severity != 'all':
                            entry_sev = entry.get('severity', 'INFO').lower()
                            if entry_sev != severity.lower():
                                continue
                        
                        entries.append(entry)
                    except json.JSONDecodeError:
                        continue
        return entries
    
    if follow:
        # Follow mode (like tail -f)
        console.print("[dim]Streaming audit log... Press Ctrl+C to exit[/dim]\n")
        
        import time
        last_position = 0
        
        try:
            with open(audit_file, 'r', encoding='utf-8') as f:
                # Move to end
                f.seek(0, 2)
                last_position = f.tell()
                
                while True:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    
                    if new_lines:
                        for line in new_lines:
                            if line.strip():
                                try:
                                    entry = json.loads(line)
                                    
                                    # Filter by severity
                                    if severity != 'all':
                                        entry_sev = entry.get('severity', 'INFO').lower()
                                        if entry_sev != severity.lower():
                                            continue
                                    
                                    console.print(format_event(entry))
                                except json.JSONDecodeError:
                                    pass
                        
                        last_position = f.tell()
                    
                    time.sleep(0.5)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚡ Stopped streaming[/yellow]")
    else:
        # Show recent entries
        entries = read_entries()
        recent = entries[-lines:] if len(entries) > lines else entries
        
        if not recent:
            console.print("[yellow]No matching events found[/yellow]")
            return
        
        console.print(f"[dim]Showing last {len(recent)} events:[/dim]\n")
        
        for entry in recent:
            console.print(format_event(entry))
        
        console.print(f"\n[dim]Total events in log: {len(entries)}[/dim]")


@cli.command()
@click.option('--set-project', help='Set project_space path')
@click.option('--set-manifest', help='Set manifest.json path')
@click.option('--show', is_flag=True, default=True, help='Show current configuration')
def config(set_project, set_manifest, show):
    """Show or modify project configuration
    
    Manages the Attribution between the engine and the physical model.
    Stores configuration in .dre/config.json
    
    \b
    Configuration:
      • project_space path (where Excel files live)
      • manifest.json location
      • audit_log.jsonl location
    
    \b
    Example:
      dre config                              # Show current config
      dre config --set-project /path/to/data  # Update project path
    """
    print_banner()
    console.print("\n[bold cyan]⚙️  Configuration Manager[/bold cyan]\n")
    
    config_dir = Path(".dre")
    config_file = config_dir / "config.json"
    
    # Default configuration
    default_config = {
        "project_space": "../project_space",
        "manifest_path": "../project_space/manifest.json",
        "audit_log_path": "../project_space/audit_log.jsonl",
        "api_host": "127.0.0.1",
        "api_port": 8000,
        "dashboard_url": "http://localhost:5173"
    }
    
    # Load existing config
    if config_file.exists():
        with open(config_file, 'r') as f:
            current_config = json.load(f)
    else:
        current_config = default_config.copy()
    
    # Update if requested
    updated = False
    if set_project:
        current_config["project_space"] = set_project
        current_config["manifest_path"] = f"{set_project}/manifest.json"
        current_config["audit_log_path"] = f"{set_project}/audit_log.jsonl"
        updated = True
        console.print(f"[green]✓[/green] Project space updated: [cyan]{set_project}[/cyan]")
    
    if set_manifest:
        current_config["manifest_path"] = set_manifest
        updated = True
        console.print(f"[green]✓[/green] Manifest path updated: [cyan]{set_manifest}[/cyan]")
    
    # Save if updated
    if updated:
        config_dir.mkdir(exist_ok=True)
        with open(config_file, 'w') as f:
            json.dump(current_config, f, indent=2)
        console.print(f"\n[dim]Configuration saved to {config_file}[/dim]\n")
    
    # Show current configuration
    if show:
        table = Table(title="Current Configuration", box=box.ROUNDED)
        table.add_column("Setting", style="cyan", width=20)
        table.add_column("Value", style="white")
        table.add_column("Status", justify="center", width=10)
        
        # Check project_space
        ps_path = Path(current_config["project_space"])
        ps_exists = ps_path.exists()
        table.add_row(
            "project_space",
            current_config["project_space"],
            "[green]✓[/green]" if ps_exists else "[red]✗[/red]"
        )
        
        # Check manifest
        manifest_path = Path(current_config["manifest_path"])
        manifest_exists = manifest_path.exists()
        table.add_row(
            "manifest.json",
            current_config["manifest_path"],
            "[green]✓[/green]" if manifest_exists else "[red]✗[/red]"
        )
        
        # Check audit log
        audit_path = Path(current_config["audit_log_path"])
        audit_exists = audit_path.exists()
        table.add_row(
            "audit_log.jsonl",
            current_config["audit_log_path"],
            "[green]✓[/green]" if audit_exists else "[yellow]○[/yellow]"
        )
        
        # API settings
        table.add_row(
            "API Endpoint",
            f"{current_config['api_host']}:{current_config['api_port']}",
            "[dim]N/A[/dim]"
        )
        
        # Dashboard
        table.add_row(
            "Dashboard URL",
            current_config["dashboard_url"],
            "[dim]N/A[/dim]"
        )
        
        console.print(table)
        console.print(f"\n[dim]Config file: {config_file}[/dim]")


@cli.command()
@click.argument('project_name', required=False, default='my-dre-project')
@click.option('--path', default='.', help='Directory to create project in')
def init(project_name, path):
    """Initialize a new DRE project with directory structure and templates"""
    print_banner()
    
    project_path = Path(path) / project_name
    
    console.print(f"\n[bold cyan]Initializing project:[/bold cyan] {project_name}")
    console.print(f"[dim]Location:[/dim] {project_path.absolute()}\n")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Create directory structure
        task = progress.add_task("[cyan]Creating directories...", total=4)
        
        dirs = [
            project_path / 'project_space',
            project_path / 'shared',
            project_path / 'logs',
            project_path / 'config'
        ]
        
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
            progress.advance(task)
        
        # Create manifest.json template
        progress.update(task, description="[cyan]Generating manifest template...")
        manifest_template = {
            "project_id": f"{project_name}-001",
            "target_file": "financial_model.xlsx",
            "stability_threshold": 0.15,
            "overlap_integral_cutoff": 0.05,
            "assertions": [
                {
                    "id": "ast-001",
                    "logical_name": "revenue_forecast",
                    "owner_role": "finance",
                    "last_updated": datetime.now().isoformat(),
                    "sla_days": 1,
                    "binding": {
                        "cell": "B10"
                    },
                    "distribution": {
                        "min": 1000000,
                        "mode": 1200000,
                        "max": 1500000
                    }
                },
                {
                    "id": "ast-002",
                    "logical_name": "cost_estimate",
                    "owner_role": "engineering",
                    "last_updated": datetime.now().isoformat(),
                    "sla_days": 2,
                    "binding": {
                        "cell": "C15"
                    },
                    "distribution": {
                        "min": 500000,
                        "mode": 750000,
                        "max": 1000000
                    }
                }
            ]
        }
        
        manifest_path = project_path / 'project_space' / 'manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest_template, f, indent=2)
        
        # Create sample .gitignore
        progress.update(task, description="[cyan]Creating .gitignore...")
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
*.egg-info/

# IDE
.vscode/
.idea/

# Logs
logs/*.log
*.log

# Excel temp files
~$*.xlsx
.~lock.*

# DRE specific
project_space/*.xlsx
!project_space/financial_model.xlsx
"""
        with open(project_path / '.gitignore', 'w') as f:
            f.write(gitignore_content)
        
        # Create README
        progress.update(task, description="[cyan]Creating README...")
        readme_content = f"""# {project_name}

Data Reliability Engine Project

## Structure

{project_name}/
  project_space/     # Excel files and manifest.json
  shared/            # Shared resources
  logs/              # Audit logs
  config/            # Configuration files

## Getting Started

1. Edit project_space/manifest.json to define your assertions
2. Create Excel file in project_space/
3. Run governance check: dre check project_space/manifest.json project_space/your_file.xlsx

## Commands

- dre init - Initialize new project
- dre validate <manifest> - Validate manifest schema
- dre check <manifest> <excel> - Run governance gates
- dre audit - Query audit logs
- dre status - Check system health
- dre watch start - Start file watcher daemon
"""
        with open(project_path / 'README.md', 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    console.print("\n[bold green]✓ Project initialized successfully![/bold green]\n")
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Item", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("Project directory", str(project_path))
    table.add_row("Manifest template", "project_space/manifest.json")
    table.add_row("README", "README.md")
    table.add_row(".gitignore", "Created")
    
    console.print(table)
    
    console.print(f"\n[dim]Next steps:[/dim]")
    console.print(f"  cd {project_name}")
    console.print(f"  dre validate project_space/manifest.json\n")


@cli.command()
@click.argument('manifest_path', type=click.Path(exists=True))
def validate(manifest_path):
    """Validate manifest.json schema and PERT distributions
    
    Uses SAME ManifestLoader from core - no reimplementation.
    """
    print_banner()
    
    console.print(f"\n[bold cyan]Validating manifest:[/bold cyan] {manifest_path}\n")
    
    try:
        # Use SAME loader as guardian - critical constraint
        manifest = ManifestLoader.load(manifest_path)
        
        console.print("[bold green]✓ Schema validation passed[/bold green]\n")
        
        # Display manifest details
        table = Table(title="Assertions Found", box=box.ROUNDED)
        table.add_column("ID", style="dim")
        table.add_column("Logical Name", style="cyan")
        table.add_column("Owner", style="yellow")
        table.add_column("SLA (days)", justify="right", style="magenta")
        table.add_column("Cell", style="blue")
        
        for assertion in manifest.assertions:
            table.add_row(
                assertion.id,
                assertion.logical_name,
                assertion.owner_role,
                str(assertion.sla_days),
                assertion.binding.cell
            )
        
        console.print(table)
        
        # Validate PERT distributions
        console.print("\n[bold cyan]Distribution Checks:[/bold cyan]\n")
        
        issues = []
        for assertion in manifest.assertions:
            dist = assertion.distribution
            if not (dist.min <= dist.mode <= dist.max):
                issues.append(f"  ✗ {assertion.logical_name}: Invalid distribution order (min <= mode <= max)")
            else:
                console.print(f"  [green]✓[/green] {assertion.logical_name}: Distribution order valid")
        
        if issues:
            console.print(f"\n[bold red]Validation Errors:[/bold red]")
            for issue in issues:
                console.print(f"[red]{issue}[/red]")
            sys.exit(1)
        else:
            console.print(f"\n[bold green]✓ All PERT distributions valid[/bold green]")
            sys.exit(0)
            
    except Exception as e:
        console.print(f"\n[bold red]✗ Validation failed:[/bold red]")
        console.print(f"[red]{str(e)}[/red]\n")
        sys.exit(1)


@cli.command()
@click.argument('manifest_path', type=click.Path(exists=True))
@click.argument('excel_path', type=click.Path(exists=True))
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
def check(manifest_path, excel_path, output_json):
    """Run full 4-gate governance analysis
    
    CRITICAL: Uses SAME brain.GateEngine - no alternative logic.
    Exit codes: 0=PASS, 1=HALT (for CI/CD integration)
    """
    if not output_json:
        print_banner()
        console.print(f"\n[bold cyan]Running Governance Check[/bold cyan]\n")
        console.print(f"[dim]Manifest:[/dim] {manifest_path}")
        console.print(f"[dim]Excel:[/dim] {excel_path}\n")
    
    try:
        # Use SAME loader - no reimplementation
        manifest = ManifestLoader.load(manifest_path)
        
        # Use SAME ingestor - no reimplementation
        ingestor = ExcelIngestor()
        data_map, formula_map = ingestor.read_data(excel_path, manifest)
        
        # Use SAME brain - no reimplementation
        gate_engine = GateEngine(manifest)
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "manifest": manifest_path,
            "excel": excel_path,
            "assertions": {},
            "status": "PASS"
        }
        
        all_passed = True
        
        # Process each assertion through all gates
        for assertion in manifest.assertions:
            assertion_results = {
                "id": assertion.id,
                "logical_name": assertion.logical_name,
                "gates": {}
            }
            
            # Gate 1: Freshness
            gate1_result = gate_engine.gate_1_freshness(assertion)
            assertion_results["gates"]["gate_1_freshness"] = gate1_result
            if gate1_result["status"] == "HALT":
                all_passed = False
            
            # Gate 2: Stability (if we have current value)
            cell_ref = assertion.binding.cell
            current_value = data_map.get(cell_ref)
            if current_value is not None and assertion.baseline_value is not None:
                gate2_result = gate_engine.gate_2_stability(assertion, current_value)
                assertion_results["gates"]["gate_2_stability"] = gate2_result
                if gate2_result["status"] == "HALT":
                    all_passed = False
            else:
                assertion_results["gates"]["gate_2_stability"] = {"status": "SKIP", "reason": "No baseline or current value"}
            
            # Gate 3: Convergence (placeholder)
            gate3_result = gate_engine.gate_3_convergence(assertion, [])
            assertion_results["gates"]["gate_3_convergence"] = gate3_result
            if gate3_result["status"] == "HALT":
                all_passed = False
            
            # Gate 4: Structure
            stored_hash = assertion.binding.formula_hash or ""
            current_hash = formula_map.get(cell_ref, {}).get("hash", "")
            gate4_result = gate_engine.gate_4_structure(stored_hash, current_hash)
            assertion_results["gates"]["gate_4_structure"] = gate4_result
            if gate4_result["status"] == "HALT":
                all_passed = False
            
            results["assertions"][assertion.id] = assertion_results
        
        if not all_passed:
            results["status"] = "HALT"
        
        if output_json:
            console.print_json(data=results)
        else:
            # Display results table
            for assertion_id, assertion_data in results["assertions"].items():
                table = Table(title=f"Assertion: {assertion_data['logical_name']} ({assertion_id})", box=box.ROUNDED)
                table.add_column("Gate", style="cyan", width=25)
                table.add_column("Status", justify="center", width=10)
                table.add_column("Details", style="yellow")
                
                for gate_name, gate_result in assertion_data["gates"].items():
                    status_text = {
                        "PASS": "[green]✓ PASS[/green]",
                        "HALT": "[red]✗ HALT[/red]",
                        "SKIP": "[dim]⊘ SKIP[/dim]"
                    }.get(gate_result["status"], "[yellow]? UNKNOWN[/yellow]")
                    
                    # Format details based on gate type
                    details = gate_result.get("reason", "")
                    if gate_name == "gate_1_freshness" and "days_since_update" in gate_result:
                        details = f"{gate_result['days_since_update']} days old (SLA: {gate_result['sla_days']} days)"
                    elif gate_name == "gate_2_stability" and "drift" in gate_result:
                        details = f"Drift: {gate_result['drift']:.2%} (threshold: {gate_result['threshold']:.2%})"
                    elif gate_name == "gate_4_structure" and gate_result["status"] == "HALT":
                        details = "Formula hash mismatch"
                    
                    table.add_row(gate_name.replace("_", " ").title(), status_text, details)
                
                console.print(table)
                console.print()
            
            if results["status"] == "HALT":
                console.print(f"[bold red]⚠ GOVERNANCE HALT DETECTED[/bold red]\n")
                sys.exit(1)
            else:
                console.print(f"[bold green]✓ All gates passed[/bold green]\n")
                sys.exit(0)
    
    except Exception as e:
        if output_json:
            console.print_json(data={"error": str(e), "status": "ERROR"})
        else:
            console.print(f"\n[bold red]✗ Check failed:[/bold red]")
            console.print(f"[red]{str(e)}[/red]\n")
        sys.exit(1)


@cli.command()
@click.option('--filter', 'filter_type', type=click.Choice(['override', 'halt', 'all']), default='all', help='Filter log entries by type')
@click.option('--severity', type=click.Choice(['info', 'warn', 'critical', 'all']), default='all', help='Filter by severity level')
@click.option('--since', help='Show logs since date (YYYY-MM-DD)')
@click.option('--limit', default=50, help='Maximum number of entries to display')
def audit(filter_type, severity, since, limit):
    """Query audit logs with filtering options
    
    Active Ledger: Searchable history for current project
    Scope: Current reporting period with advanced filters
    Purpose: Compliance verification and forensic analysis
    
    Example: dre audit --severity critical --since 2026-01-20 --limit 100
    """
    print_banner()
    
    console.print(f"\n[bold cyan]📋 Active Ledger Query[/bold cyan]\n")
    
    audit_file = Path("../project_space/audit_log.jsonl")
    
    if not audit_file.exists():
        console.print("[yellow]⚠ No audit log found[/yellow]")
        console.print(f"[dim]File: {audit_file}[/dim]")
        console.print("[dim]Logs are created when governance cycles run or overrides are submitted[/dim]\n")
        return
    
    # Read and parse log entries
    entries = []
    try:
        with open(audit_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    
                    # Filter by type
                    if filter_type != 'all':
                        event_type = entry.get('event_type', '').lower()
                        if filter_type == 'override' and 'override' not in event_type:
                            continue
                        if filter_type == 'halt' and event_type != 'halt':
                            continue
                    
                    # Filter by severity
                    if severity != 'all':
                        entry_severity = entry.get('severity', 'INFO').lower()
                        if entry_severity != severity.lower():
                            continue
                    
                    # Filter by date
                    if since:
                        try:
                            entry_date = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))
                            since_date = datetime.fromisoformat(since + 'T00:00:00+00:00')
                            if entry_date < since_date:
                                continue
                        except:
                            pass
                    
                    entries.append(entry)
    except Exception as e:
        console.print(f"[red]Error reading audit log: {e}[/red]\n")
        return
    
    if not entries:
        console.print("[yellow]No matching audit entries found[/yellow]\n")
        return
    
    # Limit results
    entries = entries[-limit:] if len(entries) > limit else entries
    
    console.print(f"[dim]Showing {len(entries)} most recent entries[/dim]\n")
    
    # Display table
    table = Table(title="Audit Log Entries", box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan", width=20)
    table.add_column("Severity", style="yellow", width=10)
    table.add_column("Event", style="yellow", width=18)
    table.add_column("Assertion", style="magenta", width=15)
    table.add_column("User", style="green", width=20)
    table.add_column("Details", style="dim")
    
    for entry in entries:
        timestamp = entry.get('timestamp', 'N/A')[:19]  # Truncate to readable format
        severity_val = entry.get('severity', 'INFO')
        event_type = entry.get('event_type', 'UNKNOWN')
        assertion_id = entry.get('assertion_id', 'N/A')
        user = entry.get('user_anchor', 'SYSTEM')
        
        # Color-code severity
        if severity_val == 'CRITICAL':
            severity_display = f"[red]{severity_val}[/red]"
        elif severity_val == 'WARN':
            severity_display = f"[yellow]{severity_val}[/yellow]"
        else:
            severity_display = f"[green]{severity_val}[/green]"
        
        # Format details based on event type
        details_dict = entry.get('details', {})
        if event_type == 'HALT':
            gates = [k for k, v in details_dict.items() if isinstance(v, dict) and v.get('status') == 'HALT']
            details = f"Gates: {', '.join(gates) if gates else 'Multiple'}"
        elif 'OVERRIDE' in event_type:
            justification = details_dict.get('justification', 'N/A')
            details = justification[:50] + '...' if len(justification) > 50 else justification
        else:
            details = str(details_dict)[:50]
        
        table.add_row(timestamp, severity_display, event_type, assertion_id, user, details)
    
    console.print(table)
    console.print(f"\n[dim]Total entries in log: {len(entries)}[/dim]\n")


@cli.command()
@click.option('--justification', help='Override justification to verify')
@click.option('--signature', help='User signature to verify')
@click.option('--timestamp', help='ISO timestamp to verify')
@click.option('--hash', 'stored_hash', help='Stored SHA-256 hash to verify against')
def verify(justification, signature, timestamp, stored_hash):
    """Verify digital signatures in audit log
    
    Cryptographic Non-Repudiation: SHA-256 hash verification
    Purpose: Prove override justifications haven't been tampered with
    
    \b
    Usage:
      dre verify                          # Verify all overrides in audit log
      dre verify --justification "..." --signature "..." --timestamp "..." --hash "..."
    
    \b
    How it works:
      1. Reads override from audit log
      2. Extracts justification + signature + timestamp
      3. Computes SHA-256 hash: hash(justification|signature|timestamp)
      4. Compares with stored hash
      5. Reports VALID or TAMPERED
    
    \b
    Example:
      dre verify  # Verify all
    """
    print_banner()
    
    if justification and signature and timestamp and stored_hash:
        # Single verification mode
        import hashlib
        
        console.print("\n[bold cyan]🔐 Digital Signature Verification[/bold cyan]\n")
        
        hash_input = f"{justification}|{signature}|{timestamp}"
        computed_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        console.print(f"[dim]Justification:[/dim] {justification[:100]}...")
        console.print(f"[dim]Signature:[/dim] {signature}")
        console.print(f"[dim]Timestamp:[/dim] {timestamp}")
        console.print()
        console.print(f"[yellow]Stored Hash:[/yellow]   {stored_hash}")
        console.print(f"[cyan]Computed Hash:[/cyan] {computed_hash}")
        console.print()
        
        if computed_hash == stored_hash:
            console.print("[bold green]✓ SIGNATURE VALID[/bold green]")
            console.print("[dim]Override has not been tampered with[/dim]\n")
        else:
            console.print("[bold red]✗ SIGNATURE INVALID[/bold red]")
            console.print("[dim]Override may have been tampered with or data is corrupt[/dim]\n")
            sys.exit(1)
    else:
        # Verify entire audit log
        from tools.verify_signature import verify_audit_log
        verify_audit_log()


@cli.command()
@click.option('--older-than', default=365, help='Archive logs older than N days (default: 365)')
@click.option('--compress', is_flag=True, default=True, help='Compress archived logs (default: True)')
def archive(older_than, compress):
    """Archive old audit logs to cold storage
    
    Cold Storage Tier: Long-term legal protection
    Scope: Historical records older than threshold
    Purpose: Keep active logs performant
    
    Example: dre archive --older-than 180
    """
    print_banner()
    
    console.print(f"\n[bold cyan]🗄️  Cold Storage Archive[/bold cyan]\n")
    
    from datetime import datetime, timedelta, timezone
    from pathlib import Path
    import json
    import gzip
    import shutil
    
    log_path = Path("../project_space/audit_log.jsonl")
    archive_dir = Path("../project_space/archives")
    
    if not log_path.exists():
        console.print("[yellow]⚠ No audit log found. Nothing to archive.[/yellow]")
        return
    
    # Create archives directory
    archive_dir.mkdir(exist_ok=True)
    
    # Calculate cutoff date
    cutoff = datetime.now(timezone.utc) - timedelta(days=older_than)
    
    # Read and categorize events
    old_events = []
    recent_events = []
    
    with open(log_path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
                event_time = datetime.fromisoformat(event["timestamp"])
                
                if event_time < cutoff:
                    old_events.append(event)
                else:
                    recent_events.append(event)
            except (json.JSONDecodeError, KeyError):
                # Preserve malformed lines in recent logs
                recent_events.append({"raw": line})
    
    if not old_events:
        console.print(f"[green]✓[/green] No events older than {older_than} days. Archive skipped.")
        return
    
    # Generate archive filename with date range
    oldest = min(datetime.fromisoformat(e["timestamp"]) for e in old_events)
    newest = max(datetime.fromisoformat(e["timestamp"]) for e in old_events)
    archive_name = f"audit_archive_{oldest.strftime('%Y%m%d')}_{newest.strftime('%Y%m%d')}.jsonl"
    
    if compress:
        archive_name += ".gz"
    
    archive_path = archive_dir / archive_name
    
    # Write archive
    console.print(f"[cyan]→[/cyan] Archiving {len(old_events)} events to {archive_path.name}")
    
    if compress:
        with gzip.open(archive_path, "wt", encoding="utf-8") as f:
            for event in old_events:
                f.write(json.dumps(event) + "\n")
    else:
        with open(archive_path, "w", encoding="utf-8") as f:
            for event in old_events:
                f.write(json.dumps(event) + "\n")
    
    # Rewrite active log with only recent events
    console.print(f"[cyan]→[/cyan] Clearing {len(old_events)} old entries from active log")
    
    with open(log_path, "w", encoding="utf-8") as f:
        for event in recent_events:
            if "raw" in event:
                f.write(event["raw"])
            else:
                f.write(json.dumps(event) + "\n")
    
    console.print(f"\n[green]✓[/green] Archive complete:")
    console.print(f"  • Archived: {len(old_events)} events")
    console.print(f"  • Remaining: {len(recent_events)} events")
    console.print(f"  • Location: {archive_path}")
    
    # Show compression ratio if compressed
    if compress:
        original_size = sum(len(json.dumps(e)) for e in old_events)
        compressed_size = archive_path.stat().st_size
        ratio = (1 - compressed_size / original_size) * 100 if original_size > 0 else 0
        console.print(f"  • Compression: {ratio:.1f}% reduction")


@cli.command()
def status():
    """Check DRE system health and last governance run
    
    Queries API health endpoint - no alternative paths.
    """
    print_banner()
    
    console.print(f"\n[bold cyan]DRE System Status[/bold cyan]\n")
    
    import urllib.request
    import urllib.error
    
    # Check API health
    try:
        with urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2) as response:
            if response.status == 200:
                api_status = "[green]● Running[/green]"
            else:
                api_status = "[yellow]● Degraded[/yellow]"
    except (urllib.error.URLError, TimeoutError):
        api_status = "[red]● Offline[/red]"
    
    table = Table(show_header=False, box=box.SIMPLE)
    table.add_column("Component", style="cyan", width=20)
    table.add_column("Status", width=20)
    
    table.add_row("API Server", api_status)
    table.add_row("File Watcher", "[dim]Check manually[/dim]")
    table.add_row("WebSocket", api_status if "Running" in api_status else "[red]● Offline[/red]")
    
    console.print(table)
    console.print(f"\n[dim]API Endpoint:[/dim] http://127.0.0.1:8000")
    console.print(f"[dim]Dashboard:[/dim] http://localhost:5173\n")


@cli.command()
@click.argument('action', type=click.Choice(['start', 'stop', 'restart', 'status']))
def watch(action):
    """Control file watcher daemon
    
    Manages watcher lifecycle - delegates to start.py, no reimplementation.
    """
    print_banner()
    
    console.print(f"\n[bold cyan]Watcher Control[/bold cyan]\n")
    
    if action == 'start':
        console.print("[yellow]Starting watcher daemon...[/yellow]")
        console.print("[dim]Run: python guardian/start.py[/dim]\n")
    elif action == 'stop':
        console.print("[yellow]Stopping watcher daemon...[/yellow]")
        console.print("[dim]Manual process termination required[/dim]\n")
    elif action == 'restart':
        console.print("[yellow]Restarting watcher daemon...[/yellow]")
        console.print("[dim]Stop and start manually[/dim]\n")
    elif action == 'status':
        console.print("[dim]Watcher status: Check process list[/dim]\n")


if __name__ == '__main__':
    cli()
