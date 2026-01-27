"""
DRE Guardian - Interactive CLI Monitor
Beautiful terminal-based governance monitoring
"""
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from datetime import datetime
import time
import sys
import subprocess
from pathlib import Path
import json

from core.loader import ManifestLoader
from core.ingestor import ExcelIngestor
from core.brain import GateEngine
from api.audit_logger import AuditLogger
from watcher.watcher import DREWatcher
from watchdog.observers import Observer
import logging

console = Console()
logger = logging.getLogger("DRE_Monitor")

class DREMonitor:
    def __init__(self, manifest_path: str, enable_dashboard: bool = False):
        self.manifest_path = manifest_path
        self.manifest = ManifestLoader.load(manifest_path)
        self.brain = GateEngine(self.manifest)
        
        # Resolve paths relative to project root (parent of guardian/)
        project_root = Path(__file__).parent.parent
        audit_path = project_root / "project_space" / "audit_log.jsonl"
        self.audit_logger = AuditLogger(str(audit_path))
        self.enable_dashboard = enable_dashboard
        
        # State tracking
        self.last_check = None
        self.total_checks = 0
        self.halt_count = 0
        self.last_status = "IDLE"
        self.current_assertions = []
        self.watching_file = None
        self.active_bypasses = {}  # Maps assertion_id -> bypass metadata
        self._frontend_process = None  # Track frontend process for cleanup
        
        # Dashboard integration
        if enable_dashboard:
            self._start_dashboard()
    
    def register_bypass(self, assertion_ids: list, justification: str, signature: str, 
                       signature_hash: str, timestamp: str, expiry_seconds: int = 3600):
        """
        Accept and validate bypass request, mutate authoritative state.
        Raises ValueError if assertion not currently in HALT.
        """
        from datetime import datetime, timedelta, timezone
        
        # Rejection condition: Can only bypass assertions currently in HALT
        for assertion_id in assertion_ids:
            # Check if assertion exists in current state
            assertion_found = False
            is_halted = False
            
            for assertion_data in self.current_assertions:
                if assertion_data["id"] == assertion_id:
                    assertion_found = True
                    gate_status = assertion_data.get("gate_status", {})
                    # Check if any gate is in HALT
                    if "HALT" in [gate_status.get("freshness"), gate_status.get("stability"), gate_status.get("alignment")]:
                        is_halted = True
                    break
            
            if not assertion_found:
                raise ValueError(f"Assertion '{assertion_id}' not found in current governance state")
            
            if not is_halted:
                raise ValueError(f"Assertion '{assertion_id}' is not in HALT state - cannot bypass")
        
        # Compute expiry timestamp
        expiry_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00')) + timedelta(seconds=expiry_seconds)
        
        # Store bypass in authoritative state
        for assertion_id in assertion_ids:
            self.active_bypasses[assertion_id] = {
                "justification": justification,
                "signature": signature,
                "signature_hash": signature_hash,
                "timestamp": timestamp,
                "expiry": expiry_time.isoformat()
            }
        
        logger.info(f"Bypass registered for assertions: {assertion_ids} (expires: {expiry_time.isoformat()})")
        
        # Immediate re-evaluation with bypass suppression applied
        self.run_governance_cycle()
        
        return True
    
    def _start_dashboard(self):
        """Start API server and frontend dev server in background for web dashboard"""
        from threading import Thread
        from api.bridge import app
        import uvicorn
        import subprocess
        
        # Start FastAPI backend
        def run_api():
            uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        
        api_thread = Thread(target=run_api, daemon=True)
        api_thread.start()
        
        # Start Vite frontend dev server
        dashboard_path = Path(__file__).parent.parent / "dashboard"
        if dashboard_path.exists():
            console.print(f"[dim]Starting frontend dev server at {dashboard_path}...[/dim]")
            try:
                # On Windows, use shell=True to find npm.cmd
                cmd = ["npm", "run", "dev"]
                self._frontend_process = subprocess.Popen(
                    cmd,
                    cwd=str(dashboard_path),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=(sys.platform == "win32"),
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
                )
                console.print(f"[green]✓[/green] Frontend dev server started (PID: {self._frontend_process.pid})")
            except FileNotFoundError:
                console.print(f"[yellow]Warning: npm not found. Please run 'npm run dev' manually in dashboard/ folder.[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not start frontend: {e}[/yellow]")
                console.print(f"[dim]Please run 'npm run dev' manually in dashboard/ folder.[/dim]")
        else:
            console.print(f"[yellow]Warning: dashboard folder not found at {dashboard_path}[/yellow]")
        
        time.sleep(2)  # Let both initialize
    
    def _get_severity_color(self, status: str) -> str:
        """Get Rich color for gate status"""
        if status == "HALT":
            return "red"
        elif status == "PASS":
            return "green"
        elif status == "WARN":
            return "yellow"
        else:
            return "dim"
    
    def _create_header(self) -> Panel:
        """Create header panel"""
        title = Text()
        title.append("⚡ ", style="bold yellow")
        title.append("DRE GUARDIAN", style="bold cyan")
        title.append(" - Live Governance Monitor", style="dim")
        
        subtitle = Text()
        subtitle.append(f"Project: {self.manifest.project_id}", style="dim")
        if self.enable_dashboard:
            subtitle.append(" │ ", style="dim")
            subtitle.append("Dashboard: http://localhost:5173", style="blue underline")
        
        return Panel(
            Text.assemble(title, "\n", subtitle),
            box=box.DOUBLE,
            style="bold white on black"
        )
    
    def _create_status_bar(self) -> Table:
        """Create status bar with metrics"""
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="left")
        table.add_column(style="white", justify="left")
        table.add_column(style="cyan", justify="left")
        table.add_column(style="white", justify="left")
        table.add_column(style="cyan", justify="left")
        table.add_column(style="white", justify="left")
        
        status_color = "red" if self.last_status == "HALT" else "green" if self.last_status == "PASS" else "yellow"
        
        table.add_row(
            "Status:", f"[{status_color}]●[/{status_color}] {self.last_status}",
            "Checks:", str(self.total_checks),
            "HALTs:", f"[red]{self.halt_count}[/red]" if self.halt_count > 0 else "0"
        )
        
        if self.last_check:
            table.add_row(
                "Last Check:", self.last_check.strftime("%H:%M:%S"),
                "Watching:", self.watching_file or "N/A",
                "", ""
            )
        
        return Panel(table, title="[bold]System Metrics[/bold]", border_style="cyan", box=box.ROUNDED)
    
    def _create_assertions_table(self) -> Panel:
        """Create live assertions table"""
        table = Table(title="Assertions", box=box.SIMPLE_HEAD, show_header=True)
        table.add_column("ID", style="magenta", width=12)
        table.add_column("Name", style="cyan", width=25)
        table.add_column("Owner", style="yellow", width=15)
        table.add_column("G1:Fresh", justify="center", width=10)
        table.add_column("G2:Stable", justify="center", width=10)
        table.add_column("G4:Struct", justify="center", width=10)
        table.add_column("Status", justify="center", width=10)
        
        if not self.current_assertions:
            table.add_row("", "[dim]Waiting for first governance cycle...[/dim]", "", "", "", "", "")
        else:
            for assertion in self.current_assertions:
                gates = assertion.get("gate_status", {})
                g1 = gates.get("freshness", "SKIP")
                g2 = gates.get("stability", "SKIP")
                g4 = gates.get("alignment", "SKIP")
                
                overall = "HALT" if "HALT" in [g1, g2, g4] else "PASS"
                
                table.add_row(
                    assertion.get("id", "N/A")[:12],
                    assertion.get("logical_name", "N/A")[:25],
                    assertion.get("owner_role", "N/A")[:15],
                    f"[{self._get_severity_color(g1)}]{g1}[/{self._get_severity_color(g1)}]",
                    f"[{self._get_severity_color(g2)}]{g2}[/{self._get_severity_color(g2)}]",
                    f"[{self._get_severity_color(g4)}]{g4}[/{self._get_severity_color(g4)}]",
                    f"[{self._get_severity_color(overall)}]{overall}[/{self._get_severity_color(overall)}]"
                )
        
        return Panel(table, border_style="green" if self.last_status == "PASS" else "red", box=box.ROUNDED)
    
    def _create_audit_log(self) -> Panel:
        """Create recent audit log panel"""
        project_root = Path(__file__).parent.parent
        audit_file = project_root / "project_space" / "audit_log.jsonl"
        
        table = Table(title="Recent Audit Trail (Last 5)", box=box.SIMPLE, show_header=True)
        table.add_column("Time", style="cyan", width=10)
        table.add_column("Event", style="yellow", width=15)
        table.add_column("Severity", justify="center", width=10)
        table.add_column("Assertion", style="magenta", width=15)
        
        if audit_file.exists():
            entries = []
            try:
                with open(audit_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            except:
                pass
            
            recent = entries[-5:] if len(entries) > 5 else entries
            recent.reverse()
            
            for entry in recent:
                timestamp = entry.get('timestamp', 'N/A')[:19].split('T')[1] if 'T' in entry.get('timestamp', '') else 'N/A'
                event = entry.get('event_type', 'UNKNOWN')[:15]
                severity = entry.get('severity', 'INFO')
                assertion_id = entry.get('assertion_id', 'N/A')[:15]
                
                sev_color = "red" if severity == "CRITICAL" else "yellow" if severity == "WARN" else "green"
                
                table.add_row(
                    timestamp,
                    event,
                    f"[{sev_color}]{severity}[/{sev_color}]",
                    assertion_id
                )
        else:
            table.add_row("", "[dim]No audit log yet[/dim]", "", "")
        
        return Panel(table, border_style="dim", box=box.ROUNDED)
    
    def _create_layout(self) -> Layout:
        """Create terminal layout"""
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=5),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=3)
        )
        
        layout["body"].split_row(
            Layout(name="main", ratio=2),
            Layout(name="sidebar", ratio=1)
        )
        
        layout["main"].split(
            Layout(name="status", size=6),
            Layout(name="assertions", ratio=1)
        )
        
        layout["header"].update(self._create_header())
        layout["status"].update(self._create_status_bar())
        layout["assertions"].update(self._create_assertions_table())
        layout["sidebar"].update(self._create_audit_log())
        layout["footer"].update(
            Panel(
                "[dim]Press Ctrl+C to exit │ File changes trigger automatic governance cycles[/dim]",
                style="dim"
            )
        )
        
        return layout
    
    def run_governance_cycle(self, filepath=None):
        """Execute governance cycle and update UI"""
        try:
            # Load current state
            ingestor = ExcelIngestor(self.manifest)
            current_state = ingestor.read_data()
            
            global_halt = False
            report = []
            
            for assertion in self.manifest.assertions:
                # Run gates
                g1 = self.brain.gate_1_freshness(assertion)
                val = current_state[assertion.id]["value"]
                g2 = self.brain.gate_2_stability(assertion, val)
                
                stored_hash = assertion.binding.formula_hash
                current_hash = current_state[assertion.id]["formula_hash"]
                g4 = self.brain.gate_4_structure(stored_hash, current_hash)
                
                # Check for raw HALT (before bypass suppression)
                raw_halt = "HALT" in [g1["status"], g2["status"], g4["status"]]
                
                # Bypass suppression layer
                is_suppressed = False
                if raw_halt and assertion.id in self.active_bypasses:
                    bypass_data = self.active_bypasses[assertion.id]
                    expiry_time = datetime.fromisoformat(bypass_data["expiry"])
                    if datetime.now(expiry_time.tzinfo) < expiry_time:
                        is_suppressed = True
                
                # Only unsuppressed HALTs contribute to system HALT
                if raw_halt and not is_suppressed:
                    global_halt = True
                    
                    # Log to audit
                    self.audit_logger.log_event(
                        event_type="HALT",
                        assertion_id=assertion.id,
                        details={
                            "gate_1_freshness": g1,
                            "gate_2_stability": g2,
                            "gate_4_structure": g4
                        },
                        user=assertion.owner_role,
                        severity="CRITICAL"
                    )
                
                report.append({
                    "id": assertion.id,
                    "logical_name": assertion.logical_name,
                    "owner_role": assertion.owner_role,
                    "gate_status": {
                        "freshness": g1["status"],
                        "stability": g2["status"],
                        "alignment": g4["status"]
                    },
                    "gate_details": {
                        "freshness": g1,
                        "stability": g2,
                        "alignment": g4
                    },
                    "distribution": assertion.distribution.dict()
                })
            
            # Update state
            self.last_check = datetime.now()
            self.total_checks += 1
            self.last_status = "HALT" if global_halt else "PASS"
            if global_halt:
                self.halt_count += 1
            self.current_assertions = report
            
            # Push to dashboard if enabled
            if self.enable_dashboard:
                try:
                    # Store state in API for frontend to poll
                    import api.bridge as bridge_module
                    from datetime import timezone
                    
                    governance_state = {
                        "status": self.last_status,
                        "assertions": report,
                        "conflict_pair": None,
                        "last_updated": datetime.now(timezone.utc).isoformat()
                    }
                    bridge_module.current_governance_state = governance_state
                    
                    # Only open browser on HALT
                    if global_halt:
                        import webbrowser
                        webbrowser.open("http://localhost:5173")
                except:
                    pass
        
        except Exception as e:
            self.last_status = f"ERROR: {str(e)[:30]}"
    
    def start_monitoring(self, watch_path: str = None):
        """Start live monitoring with file watcher"""
        # Resolve watch path to absolute project_space directory
        if watch_path is None:
            project_root = Path(__file__).parent.parent
            watch_path = str(project_root / "project_space")
        
        self.watching_file = f"{watch_path}/{self.manifest.target_file}"
        
        # Register this monitor instance with Bridge for command ingress
        if self.enable_dashboard:
            import api.bridge as bridge_module
            bridge_module.monitor_instance = self
        
        # Run initial check
        self.run_governance_cycle()
        
        # Setup file watcher
        watcher = DREWatcher(
            callback=self.run_governance_cycle,
            target_file=self.watching_file,
            debounce_seconds=0.9
        )
        
        observer = Observer()
        observer.schedule(watcher, path=watch_path, recursive=False)
        observer.start()
        
        # Live display loop
        try:
            last_state = None
            with Live(self._create_layout(), console=console, refresh_per_second=0.5, screen=True) as live:
                while True:
                    # Only update if state changed
                    current_state = (self.last_status, self.total_checks, self.halt_count, len(self.current_assertions))
                    if current_state != last_state:
                        live.update(self._create_layout())
                        last_state = current_state
                    time.sleep(2)
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
            
            # Cleanup frontend process
            if self._frontend_process:
                try:
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(self._frontend_process.pid)], 
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        self._frontend_process.terminate()
                        self._frontend_process.wait(timeout=2)
                except:
                    pass
            
            console.print("\n[yellow]⚡ Guardian stopped[/yellow]")


if __name__ == "__main__":
    import sys
    
    # Parse args
    enable_dashboard = "--dashboard" in sys.argv or "-d" in sys.argv
    manifest_path = "../project_space/manifest.json"
    
    # Banner
    console.print("\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]")
    console.print("[bold yellow]⚡ DRE GUARDIAN[/bold yellow] [dim]- Data Reliability Engine[/dim]")
    console.print("[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n")
    
    if enable_dashboard:
        console.print("[green]✓[/green] Dashboard enabled: [blue underline]http://localhost:5173[/blue underline]")
    
    console.print("[dim]Loading manifest...[/dim]\n")
    
    try:
        monitor = DREMonitor(manifest_path, enable_dashboard=enable_dashboard)
        monitor.start_monitoring()
    except FileNotFoundError:
        console.print("[red]✗ Manifest not found. Run:[/red] [cyan]dre init[/cyan]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Error:[/red] {e}")
        sys.exit(1)
