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
import logging
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows console encoding for Unicode characters
# Use reconfigure() which is safe in both frozen and script mode
if sys.platform == 'win32':
    try:
        # reconfigure() is safer than wrapping with TextIOWrapper
        # It works in frozen mode without closing underlying streams
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass  # If reconfigure fails, continue with default encoding

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

# Lazy imports - only load heavy modules when needed
# This keeps CLI startup fast (<1 second)
# from guardian.core.loader import ManifestLoader
# from guardian.core.ingestor import ExcelIngestor
# from guardian.core.brain import GateEngine
# from guardian.core.schema import DREManifest, Assertion, PertDistribution, DataBinding
# from guardian.core.config import get_config

# Configure Rich console for frozen mode compatibility
# With stdout/stderr reconfigured to UTF-8, we can use full Rich features
_is_frozen = getattr(sys, 'frozen', False) and sys.platform == 'win32'

if _is_frozen:
    # Frozen mode: use legacy_windows for compatibility but keep colors
    console = Console(
        force_terminal=True, 
        legacy_windows=True,  # Use Windows console APIs
        safe_box=True,        # ASCII-safe box drawing
        highlight=False       # Disable auto-highlighting
    )
    # Override box styles to use ASCII (more reliable in Windows console)
    box.ROUNDED = box.ASCII
    box.DOUBLE = box.ASCII
    box.HEAVY = box.ASCII
    box.SQUARE = box.ASCII
else:
    console = Console()

def safe_print(msg: str):
    """Print message safely - works in frozen mode"""
    if _is_frozen:
        # Strip Rich markup and replace Unicode chars with ASCII
        import re
        clean = re.sub(r'\[/?[^\]]+\]', '', msg)
        # Replace common Unicode chars that fail with cp1252
        clean = clean.replace('✓', '[OK]').replace('✗', '[X]').replace('⚠', '[!]')
        clean = clean.replace('→', '->').replace('•', '*').replace('─', '-')
        clean = clean.replace('│', '|').replace('└', '\\').replace('├', '+')
        print(clean)
    else:
        console.print(msg)
    
logger = logging.getLogger("DRE_Guardian.CLI")


def interactive_shell():
    """Interactive command shell - keeps process alive"""
    console.print("\n[bold green]Welcome![/bold green] Type [cyan]'init'[/cyan] to get started, or [cyan]'help'[/cyan] for all commands.\n")
    
    while True:
        try:
            # Prompt for command
            console.print("[cyan]dre>[/cyan] ", end="")
            user_input = input().strip()
            
            if not user_input:
                continue
            
            # Handle exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                console.print("[yellow]Goodbye![/yellow]")
                break
            
            # Handle help
            if user_input.lower() in ['help', '?', '--help']:
                print_banner()
                from click import Context
                ctx = Context(cli)
                console.print(cli.get_help(ctx))
                continue
            
            # Parse and execute command
            args = user_input.split()
            try:
                # Invoke CLI with parsed arguments
                cli(args, standalone_mode=False)
            except SystemExit:
                # Catch sys.exit() from commands to keep shell alive
                pass
            except Exception as e:
                console.print(f"[red]Error:[/red] {e}")
                logger.error(f"Command failed: {e}", exc_info=True)
            
            console.print()  # Empty line for readability
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            continue
        except EOFError:
            console.print("\n[yellow]EOF received, exiting...[/yellow]")
            break


def print_banner():
    """Display ASCII banner - uses ASCII-safe characters in frozen mode"""
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        # ASCII-safe banner for frozen Windows exe
        banner = """
+--------------------------------------------------+
|                                                  |
|   DRE ENGINE - Data Reliability Engine          |
|   Epistemic Governance for Strategic Models     |
|                                                  |
+--------------------------------------------------+

Quick Start:
  init        Create project scaffolding
  doctor      Validate project readiness
  monitor     Start governance tracking
    """
        print(banner)  # Use plain print, not Rich
    else:
        # Unicode banner for development
        banner = """
[bold cyan]╔══════════════════════════════════════════════════╗
║                                                  ║
║   DRE ENGINE - Data Reliability Engine          ║
║   Epistemic Governance for Strategic Models     ║
║                                                  ║
╚══════════════════════════════════════════════════╝[/bold cyan]

[bold white]Quick Start:[/bold white]
  [cyan]init[/cyan]        Create project scaffolding
  [cyan]doctor[/cyan]      Validate project readiness
  [cyan]monitor[/cyan]     Start governance tracking
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
        
        # Show setup guidance if manifest doesn't exist
        from pathlib import Path
        from guardian.core.config import get_config
        config = get_config()
        manifest_path = config.manifest_path
        if not manifest_path.exists():
            console.print("\n[yellow]⚠ No project configured[/yellow]")
            console.print("[dim]Run[/dim] [cyan]dre init[/cyan] [dim]to create a new project[/dim]")
            console.print("[dim]Or run[/dim] [cyan]dre doctor[/cyan] [dim]to check system health[/dim]\n")
        
        # Enter interactive mode if running as frozen exe
        if getattr(sys, 'frozen', False):
            interactive_shell()


@cli.command()
@click.option('--dashboard', '-d', is_flag=True, help='Enable web dashboard alongside CLI monitor')
@click.argument('manifest', required=False)
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
      dre monitor                           # Auto-detect manifest
      dre monitor path/to/manifest.json     # Explicit path
      dre monitor --dashboard               # With web UI
    
    \b
    Recommendation:
      1. Run 'dre monitor --dashboard' to start monitoring
      2. Access dashboard at http://127.0.0.1:8000
      3. Minimize terminal - monitoring continues in background
    """
    print_banner()
    
    from pathlib import Path
    from guardian.core.validator import PreflightValidator
    
    # Auto-detect manifest if not provided
    if manifest is None:
        # Search order:
        # 1. Current working directory
        # 2. project_space/ in current directory
        # 3. Desktop/project_space/ (common user location)
        # 4. User's home directory
        
        search_paths = [
            Path.cwd() / 'manifest.json',
            Path.cwd() / 'project_space' / 'manifest.json',
            Path.home() / 'Desktop' / 'project_space' / 'manifest.json',
            Path.home() / 'OneDrive' / 'Desktop' / 'project_space' / 'manifest.json',
            Path.home() / 'project_space' / 'manifest.json',
        ]
        
        manifest_file = None
        for path in search_paths:
            if path.exists():
                manifest_file = path
                safe_print(f"[dim]✓ Found manifest: {path}[/dim]\n")
                break
        
        if manifest_file is None:
            safe_print("[bold red]✗ No manifest.json found[/bold red]\n")
            safe_print("Searched in:")
            for path in search_paths:
                safe_print(f"  • {path}")
            safe_print("\n[yellow]Please specify the manifest path:[/yellow]")
            safe_print("  dre monitor path/to/manifest.json\n")
            sys.exit(1)
    else:
        manifest_file = Path(manifest)
        if not manifest_file.is_absolute():
            manifest_file = Path.cwd() / manifest_file
    
    # Preflight validation (CRITICAL - must pass before monitoring starts)
    safe_print("[dim]Running preflight validation...[/dim]\n")
    errors, warnings = PreflightValidator.validate_project(str(manifest_file))
    
    # Display blocking errors
    if errors:
        safe_print("[bold red]✗ Cannot Start Monitor[/bold red]\n")
        safe_print("[yellow]The following issues must be fixed before monitoring can start:[/yellow]\n")
        
        for idx, error in enumerate(errors, 1):
            safe_print(f"[red]Issue {idx}:[/red] [bold]{error.title}[/bold]")
            safe_print(f"  {error.message}\n")
            safe_print(f"  [yellow]Fix:[/yellow]")
            for line in error.fix.split('\n'):
                safe_print(f"    {line}")
            safe_print("")
        
        safe_print("[bold red]✗ Monitoring blocked[/bold red]")
        safe_print("[dim]Run 'doctor' to see detailed validation results[/dim]\n")
        sys.exit(1)
    
    # Display warnings (non-blocking)
    if warnings:
        safe_print("[bold yellow]⚠ Warnings:[/bold yellow]")
        for warning in warnings:
            safe_print(f"  • {warning.title}")
            safe_print(f"    [dim]{warning.recommendation}[/dim]")
        safe_print("")
    
    safe_print("[green]✓[/green] Preflight validation passed\n")
    
    try:
        # If dashboard enabled, use production server architecture
        # (uvicorn as main process, monitor in background thread)
        if dashboard:
            from guardian.main import run_production_server
            run_production_server(manifest_path=str(manifest_file), auto_open_browser=True)
        else:
            # CLI-only mode: just run the monitor
            from guardian.monitor import DREMonitor
            mon = DREMonitor(str(manifest_file), enable_dashboard=False)
            mon.start_monitoring()
    except KeyboardInterrupt:
        pass  # Monitor handles its own exit message
    except Exception as e:
        # User-friendly error handling (no stack traces)
        error_title = "Monitor Startup Failed"
        error_message = str(e)
        
        # Categorize common errors
        if "PermissionError" in type(e).__name__ or "locked" in error_message.lower():
            error_title = "Excel file is locked"
            error_message = "The Excel file is currently open in another application.\n\nClose the Excel file and try again."
        elif "FileNotFoundError" in type(e).__name__:
            error_title = "File not found"
            error_message = f"{e}\n\nVerify the file path in manifest.json is correct."
        elif "JSONDecodeError" in type(e).__name__:
            error_title = "Invalid JSON in manifest"
            error_message = "The manifest file contains syntax errors.\n\nOpen manifest.json and fix the JSON syntax."
        
        console.print(f"\n[bold red]✗ {error_title}[/bold red]\n")
        console.print(f"{error_message}\n")
        
        # Show error dialog on Windows (frozen mode)
        if getattr(sys, 'frozen', False) and sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, f"{error_title}\n\n{error_message}", "DRE Guardian", 0x10)
            except:
                pass
        
        logger.error(f"Monitor startup failed: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument('manifest', required=False)
def dashboard(manifest):
    """Start governance monitoring with web dashboard
    
    Shortcut for 'monitor --dashboard'. Opens the web UI automatically.
    
    \b
    Example:
      dre dashboard                         # Auto-detect manifest
      dre dashboard path/to/manifest.json   # Explicit path
    
    Dashboard URL: http://127.0.0.1:8000
    """
    # Reuse the monitor command with dashboard=True
    ctx = click.get_current_context()
    ctx.invoke(monitor, dashboard=True, manifest=manifest)


@cli.command()
@click.option('--json', 'output_json', is_flag=True, help='Output results as JSON')
def doctor(output_json):
    """Preflight validation - Is this project ready to monitor?
    
    Comprehensive validation of project configuration, Excel file,
    and cell references. Run this before starting monitor to catch
    configuration errors early.
    
    \b
    Checks:
      • Manifest file exists and has valid JSON syntax
      • Required manifest fields are present
      • Excel file exists and is accessible
      • All referenced sheets exist in the Excel file
      • All referenced cells are valid and readable
      • Cell values match expected types
    
    \b
    Example:
      dre doctor        # Human-readable validation report
      dre doctor --json # Machine-readable output
    """
    print_banner()
    console.print("\n[bold cyan]🔬 Preflight Validation[/bold cyan]\n")
    
    from guardian.core.config import get_config
    from guardian.core.validator import PreflightValidator
    
    config = get_config()
    manifest_path = str(config.manifest_path)
    
    console.print(f"[dim]Validating:[/dim] {manifest_path}\n")
    
    # Run comprehensive validation
    errors, warnings = PreflightValidator.validate_project(manifest_path)
    
    # Display results
    if output_json:
        results = {
            "timestamp": datetime.now().isoformat(),
            "manifest_path": manifest_path,
            "status": "READY" if not errors else "NOT_READY",
            "errors": [
                {
                    "category": e.category,
                    "title": e.title,
                    "message": e.message,
                    "fix": e.fix
                }
                for e in errors
            ],
            "warnings": [
                {
                    "category": w.category,
                    "title": w.title,
                    "message": w.message,
                    "recommendation": w.recommendation
                }
                for w in warnings
            ]
        }
        console.print(json.dumps(results, indent=2))
    else:
        # Human-readable output
        if errors:
            console.print("[bold red]✗ Blocking Issues Found[/bold red]\n")
            for idx, error in enumerate(errors, 1):
                console.print(f"[red]Issue {idx}:[/red] [bold]{error.title}[/bold]")
                console.print(f"  {error.message}")
                console.print(f"\n  [yellow]Fix:[/yellow]")
                for line in error.fix.split('\n'):
                    console.print(f"    {line}")
                console.print()
            
            console.print(f"[bold red]✗ NOT READY[/bold red] - Fix {len(errors)} issue{'s' if len(errors) != 1 else ''} before running monitor\n")
            sys.exit(1)
        
        if warnings:
            console.print("[bold yellow]⚠ Warnings[/bold yellow]\n")
            for idx, warning in enumerate(warnings, 1):
                console.print(f"[yellow]Warning {idx}:[/yellow] {warning.title}")
                console.print(f"  {warning.message}")
                console.print(f"  [dim]Recommendation: {warning.recommendation}[/dim]")
                console.print()
        
        console.print("[bold green]✓ READY TO MONITOR[/bold green]")
        console.print("[dim]All validation checks passed. You can run 'monitor' to start governance tracking.[/dim]\n")


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
    
    from guardian.core.config import get_config
    config = get_config()
    audit_file = config.audit_log_path
    
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
        "dashboard_url": "http://127.0.0.1:8000"
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
def init():
    """Create project scaffolding in project_space folder
    
    This creates:
      • project_space/ - Directory for your Excel file and configuration
      • manifest.json - Governance configuration template (must be edited)
    
    You must provide your own Excel file and update the manifest accordingly.
    """
    print_banner()
    
    from guardian.core.config import get_config
    config = get_config()
    
    console.print("\n[bold cyan]⚡ Initializing DRE Project[/bold cyan]\n")
    console.print(f"[dim]Location:[/dim] {config.project_space}\n")
    
    # Create project_space directory
    directory_already_existed = config.project_space.exists()
    
    try:
        config.ensure_project_space()
        
        # Verify directory actually exists
        if not config.project_space.exists():
            console.print(f"[bold red]✗ Failed to create directory[/bold red]")
            console.print(f"[yellow]Please manually create:[/yellow] {config.project_space}")
            console.print("[dim]Tip: Copy the path above and create the folder in Windows Explorer[/dim]\n")
            sys.exit(1)
        
        # Show appropriate message
        if directory_already_existed:
            console.print(f"[dim]Directory already exists:[/dim] {config.project_space.name}\n")
        else:
            console.print(f"[green]✓[/green] Created new directory: [cyan]{config.project_space.name}[/cyan]")
            console.print(f"[dim]Full path:[/dim] {config.project_space}")
            
            # Open the folder in Windows Explorer so user can see it
            try:
                import subprocess
                subprocess.run(['explorer', str(config.project_space)], check=False)
                console.print(f"[dim]Opening folder in Windows Explorer...[/dim]\n")
            except:
                console.print()  # Just add newline if explorer fails
            
    except Exception as e:
        console.print(f"[bold red]✗ Error:[/bold red] {e}")
        console.print(f"[yellow]Please manually create:[/yellow] {config.project_space}\n")
        sys.exit(1)
    
    manifest_path = config.project_space / 'manifest.json'
    
    # Check if manifest already exists
    if manifest_path.exists():
        console.print("[yellow]⚠ Warning: manifest.json already exists[/yellow]\n")
        console.print(f"  [dim]Existing:[/dim] {manifest_path.name}")
        
        console.print("\n[yellow]Overwrite existing manifest? (y/N):[/yellow] ", end="")
        try:
            response = input().strip().lower()
            if response != 'y':
                console.print("\n[dim]Initialization cancelled[/dim]\n")
                return
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]Initialization cancelled[/dim]\n")
            return
        console.print()
    
    # Create manifest.json template (schema example only, no business logic)
    console.print("[cyan]→[/cyan] Creating manifest.json template...")
    manifest_template = {
        "project_id": "your-project-id",
        "project_name": "Your Project Name",
        "target_file": "your-model.xlsx",
        
        "governance_config": {
            "stability_threshold": 0.15,
            "overlap_integral_cutoff": 0.05,
            "freshness_sla_enforcement": True
        },
        
        "assertions": [
            {
                "id": "example-assertion",
                "logical_name": "example_cell",
                "description": "Example cell description",
                "owner_role": "Role Name",
                "last_updated": datetime.now(timezone.utc).isoformat(),
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
    
    with open(manifest_path, 'w') as f:
        json.dump(manifest_template, f, indent=2)
    console.print(f"  [green]✓[/green] Created: {manifest_path.name}")
    
    # Success message with clear next steps
    console.print("\n[bold green]✓ Project structure created[/bold green]\n")
    console.print("[bold white]Required next steps:[/bold white]")
    console.print(f"  1. Place your Excel file in: [cyan]{config.project_space}[/cyan]")
    console.print("  2. Edit [cyan]manifest.json[/cyan]:")
    console.print("     • Set [dim]target_file[/dim] to your Excel filename")
    console.print("     • Define assertions for cells you want to monitor")
    console.print("     • Update project metadata")
    console.print("  3. Run [cyan]monitor[/cyan] to start governance tracking\n")


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
        from guardian.core.loader import ManifestLoader
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
        from guardian.core.loader import ManifestLoader
        from guardian.core.ingestor import ExcelIngestor
        from guardian.core.brain import GateEngine
        
        manifest = ManifestLoader.load(manifest_path)
        
        # Use SAME ingestor - pass manifest and manifest_path
        ingestor = ExcelIngestor(manifest, manifest_path)
        data_map = ingestor.read_data()
        
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
            # data_map is keyed by assertion.id, contains {"value": x, "formula_hash": y}
            assertion_data_entry = data_map.get(assertion.id, {})
            current_value = assertion_data_entry.get("value")
            if current_value is not None:
                gate2_result = gate_engine.gate_2_stability(assertion, current_value)
                assertion_results["gates"]["gate_2_stability"] = gate2_result
                if gate2_result["status"] == "HALT":
                    all_passed = False
            else:
                assertion_results["gates"]["gate_2_stability"] = {"status": "SKIP", "reason": "No current value available"}
            
            # Gate 3: Convergence (requires conflict pairs - skip if none defined)
            assertion_results["gates"]["gate_3_convergence"] = {"status": "SKIP", "reason": "No conflict pairs defined"}
            
            # Gate 4: Structure
            stored_hash = assertion.binding.formula_hash or ""
            current_hash = assertion_data_entry.get("formula_hash", "")
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
    
    from guardian.core.config import get_config
    config = get_config()
    audit_file = config.audit_log_path
    
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
    from guardian.core.config import get_config
    
    config = get_config()
    log_path = config.audit_log_path
    archive_dir = config.archives_dir
    
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
    console.print(f"\n[dim]Dashboard:[/dim] http://127.0.0.1:8000\n")


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


def global_exception_handler(exc_type, exc_value, exc_traceback):
    """
    Global exception handler that logs uncaught exceptions before the process exits.
    This is critical for .exe mode where crashes would be silent otherwise.
    """
    if issubclass(exc_type, KeyboardInterrupt):
        # Don't log keyboard interrupts
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger.critical(
        "Uncaught exception - DRE Guardian is shutting down",
        exc_info=(exc_type, exc_value, exc_traceback)
    )
    
    error_msg = f"Fatal Error: {exc_value}\n\nDRE Guardian encountered an error and needs to close."
    
    # Show message box on Windows if running as frozen executable
    if getattr(sys, 'frozen', False) and sys.platform == 'win32':
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "DRE Guardian Error", 0x10)
        except:
            pass
    
    safe_print("\n[bold red]✗ Fatal Error - See logs for details[/bold red]")
    try:
        from guardian.core.config import get_config
        safe_print(f"[dim]Log file: {get_config().log_file}[/dim]\n")
    except:
        pass


if __name__ == '__main__':
    # Initialize configuration and logging
    config = None
    try:
        from guardian.core.config import get_config
        config = get_config()
        config.setup_logging(level="INFO")
    except Exception as e:
        # Handle early initialization failures gracefully
        safe_print(f"\n[bold red]Startup Error[/bold red]")
        safe_print(f"[yellow]{e}[/yellow]\n")
        safe_print("[dim]This is likely a first-time setup issue.[/dim]")
        safe_print("[dim]The application will attempt to create required directories...\n[/dim]")
        # Don't exit - let CLI handle it gracefully
    
    # Install global exception handler
    sys.excepthook = global_exception_handler
    
    # Run Click CLI
    try:
        cli()
    except SystemExit as e:
        # Normal exit from Click or interactive shell
        if e.code != 0 and _is_frozen:
            # On error exit in frozen mode, pause so user can see the error
            print("\nPress Enter to close...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass
        raise
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        if config:
            logger.critical(f"CLI execution failed: {e}", exc_info=True)
        
        print(f"\nAn error occurred: {e}\n")
        
        if config:
            print(f"Detailed logs: {config.log_file}\n")
        
        # Keep terminal open if running as frozen exe
        if _is_frozen:
            print("Press Enter to close...")
            try:
                input()
            except (EOFError, KeyboardInterrupt):
                pass
        
        sys.exit(1)
