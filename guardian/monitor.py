"""
DRE Guardian - Interactive CLI Monitor
Beautiful terminal-based governance monitoring
"""
import sys
import os
# Force UTF-8 encoding for Windows compatibility
# But only in non-frozen mode - PyInstaller handles this differently
if sys.platform == "win32" and not getattr(sys, 'frozen', False):
    os.environ["PYTHONIOENCODING"] = "utf-8"
    # Reconfigure stdout/stderr for UTF-8 only if buffer is available
    try:
        import io
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer is not None:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer is not None:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # In frozen mode, just use default encoding

from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.style import Style
from rich import box
from datetime import datetime, timezone, timedelta
import time
import sys
import subprocess
from pathlib import Path
import json

from guardian.core.loader import ManifestLoader
from guardian.core.ingestor import ExcelIngestor
from guardian.core.brain import GateEngine
from guardian.core.config import get_config
from guardian.api.audit_logger import AuditLogger
from guardian.watcher.watcher import DREWatcher
from watchdog.observers import Observer
import logging
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    Icon = Menu = MenuItem = Image = ImageDraw = None
try:
    from pystray import Icon, Menu, MenuItem
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# Theme Configuration - Matches Dashboard Styling
# ═══════════════════════════════════════════════════════════════════════════════
class Theme:
    """Unified theme matching dashboard design"""
    # Primary colors from dashboard
    CYAN = "#00D4FF"
    GREEN = "#00FF88"
    YELLOW = "#FFD93D"
    RED = "#FF6B6B"
    PURPLE = "#A855F7"
    ORANGE = "#FF8C42"
    
    # Neutral tones
    DIM = "#6B7280"
    MUTED = "#9CA3AF"
    WHITE = "#FFFFFF"
    
    # Status colors
    PASS = GREEN
    HALT = RED
    WARN = YELLOW
    
    # Semantic styles
    HEADER = Style(color=CYAN, bold=True)
    TITLE = Style(color=WHITE, bold=True)
    ACCENT = Style(color=GREEN, bold=True)
    STATUS_PASS = Style(color=GREEN, bold=True)
    STATUS_HALT = Style(color=RED, bold=True)
    STATUS_WARN = Style(color=YELLOW, bold=True)
    SUBTLE = Style(color=DIM)
    LINK = Style(color=CYAN, underline=True)


# Configure Rich console for frozen mode compatibility
_is_frozen = getattr(sys, 'frozen', False) and sys.platform == 'win32'

if _is_frozen:
    import os
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    console = Console(
        force_terminal=True, 
        legacy_windows=True, 
        no_color=True,
        safe_box=True,
        highlight=False
    )
    # Override default box to use ASCII
    box.ROUNDED = box.ASCII
    box.DOUBLE = box.ASCII
    box.HEAVY = box.ASCII
    box.SQUARE = box.ASCII
else:
    console = Console()

def safe_print(msg: str):
    """Print message safely - works in frozen mode"""
    if _is_frozen:
        import re
        clean = re.sub(r'\[/?[^\]]+\]', '', msg)
        print(clean)
    else:
        console.print(msg)
    
logger = logging.getLogger("DRE_Monitor")

class DREMonitor:
    def __init__(self, manifest_path: str = None, enable_dashboard: bool = False):
        # Initialize configuration
        self.config = get_config(manifest_path)
        
        self.manifest_path = str(self.config.manifest_path)
        self.manifest = ManifestLoader.load(self.manifest_path)
        self.brain = GateEngine(self.manifest)
        
        # Use config for audit logger
        self.audit_logger = AuditLogger(self.config.audit_log_path)
        self.enable_dashboard = enable_dashboard
        
        # State tracking
        self.last_check = None
        self.total_checks = 0
        self.halt_count = 0
        self._api_port = 8000  # Default, updated if different port used
        self.last_status = "IDLE"
        self.current_assertions = []
        self.watching_file = None
        self.active_bypasses = {}  # Maps assertion_id -> bypass metadata
        self._frontend_process = None  # Track frontend process for cleanup
        self._api_process = None  # Track uvicorn subprocess for cleanup
        self.tray_icon = None  # System tray icon
        
        # Dashboard integration
        if enable_dashboard:
            self._start_dashboard()
            if TRAY_AVAILABLE:
                self._init_tray_icon()
    
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
    
    def run(self):
        """
        Run monitor in background mode (no TUI)
        
        This is called when the monitor runs as a background thread
        alongside the uvicorn server (production server architecture).
        """
        # Resolve watch path
        manifest_dir = Path(self.manifest_path).parent
        watch_path = str(manifest_dir)
        self.watching_file = f"{watch_path}/{self.manifest.target_file}"
        
        # Register this monitor instance with Bridge
        import guardian.api.bridge as bridge_module
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
        
        try:
            # Keep thread alive, checking periodically
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
    
    def _start_dashboard(self):
        """Start API server to serve static dashboard from bundled dist/ folder"""
        import subprocess
        import sys
        
        # Verify dashboard build exists (using config that was initialized with manifest_path)
        dashboard_dist = self.config.dashboard_dir / "dist"
        
        if not dashboard_dist.exists():
            console.print(f"[red]✗ Dashboard build not found at {dashboard_dist}[/red]")
            console.print(f"[yellow]Build dashboard first: cd dashboard && npm run build[/yellow]")
            console.print(f"[dim]Looking in: {dashboard_dist}[/dim]")
            console.print(f"[dim]Is frozen: {self.config.is_frozen}[/dim]")
            console.print(f"[dim]Bundle dir: {self.config.bundle_dir}[/dim]")
            return
        
        console.print(f"[dim]✓ Dashboard found at {dashboard_dist}[/dim]")
        
        # Find available port
        import socket
        def find_available_port(start_port=8000, max_attempts=3):
            for port in range(start_port, start_port + max_attempts):
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('127.0.0.1', port))
                        return port
                except OSError:
                    continue
            return None
        
        port = find_available_port()
        if port is None:
            console.print(f"[red]✗ Ports 8000-8002 are all in use[/red]")
            console.print(f"[yellow]Close other applications and try again[/yellow]")
            return
        
        self._api_port = port
        
        # Start uvicorn server
        try:
            # In frozen mode (exe), run uvicorn in a background thread
            # In script mode, use subprocess for better isolation
            if getattr(sys, 'frozen', False):
                # Frozen mode: run uvicorn in background thread
                from threading import Thread
                import uvicorn
                from guardian.api import bridge
                
                console.print(f"[dim]Starting dashboard server in background thread...[/dim]")
                
                def run_uvicorn():
                    uvicorn.run(
                        bridge.app,
                        host="127.0.0.1",
                        port=port,
                        log_level="info",
                        access_log=False
                    )
                
                server_thread = Thread(target=run_uvicorn, daemon=True)
                server_thread.start()
                self._api_process = server_thread  # Store for tracking
            else:
                # Script mode: run as subprocess
                python_exe = sys.executable
                
                # Create log file in project directory
                log_file = self.config.manifest_path.parent / "uvicorn.log"
                
                if sys.platform == "win32":
                    with open(log_file, "w") as f:
                        pass  # Create/clear the file
                    
                    self._api_process = subprocess.Popen(
                        [python_exe, "-m", "uvicorn", "guardian.api.bridge:app",
                         "--host", "127.0.0.1", "--port", str(port),
                         "--log-level", "info"],
                        stdout=open(log_file, "a"),
                        stderr=subprocess.STDOUT,
                        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                        cwd=str(Path(__file__).parent.parent)
                    )
                else:
                    import os as os_module
                    with open(log_file, "w") as f:
                        pass
                        
                    self._api_process = subprocess.Popen(
                        [python_exe, "-m", "uvicorn", "guardian.api.bridge:app",
                         "--host", "127.0.0.1", "--port", str(port),
                         "--log-level", "info"],
                        stdout=open(log_file, "a"),
                        stderr=subprocess.STDOUT,
                        preexec_fn=os_module.setsid,
                        cwd=str(Path(__file__).parent.parent)
                    )
            
            dashboard_url = f"http://127.0.0.1:{port}"
            console.print(f"[green]\u2713[/green] Dashboard server started at [bold blue]{dashboard_url}[/bold blue]")
            console.print(f"[dim]Server logs: {log_file}[/dim]")
            
            time.sleep(3)  # Let server initialize
            
            # Auto-open browser
            import webbrowser
            try:
                console.print(f"[yellow]→[/yellow] Attempting to open dashboard in browser...")
                opened = webbrowser.open(dashboard_url)
                if opened:
                    console.print(f"[green]✓[/green] Dashboard opened in browser\n")
                else:
                    console.print(f"[yellow]⚠[/yellow] Browser may not have opened automatically")
                    console.print(f"[bold]→ Please manually open:[/bold] [bold blue]{dashboard_url}[/bold blue]\n")
            except Exception as e:
                console.print(f"[yellow]⚠[/yellow] Could not auto-open browser: {e}")
                console.print(f"[bold]→ Please manually open:[/bold] [bold blue]{dashboard_url}[/bold blue]\n")
        except Exception as e:
            console.print(f"[red]✗ Failed to start dashboard server: {e}[/red]")
            logger.error(f"Dashboard startup error: {e}", exc_info=True)
    
    def _init_tray_icon(self):
        """Initialize system tray icon (Windows notification area) - Silent Guardian"""
        if not TRAY_AVAILABLE:
            console.print("[yellow]Note: pystray not installed. Install with: pip install pystray pillow[/yellow]")
            return
        
        from threading import Thread
        
        # Create tray icon wrapper
        class TrayIconWrapper:
            def __init__(self, manifest_name):
                self.manifest_name = manifest_name
                self.icon = None
                self.halt_active = False
                
            def create_image(self, color="green"):
                """Create shield icon image"""
                size = 64
                image = Image.new('RGB', (size, size), 'white')
                draw = ImageDraw.Draw(image)
                
                # Draw shield shape
                shield_color = {
                    "green": (46, 204, 113),
                    "red": (231, 76, 60),
                    "yellow": (241, 196, 15)
                }[color]
                
                points = [(size//2, 10), (size-10, size//3), (size-10, size*2//3), 
                          (size//2, size-5), (10, size*2//3), (10, size//3)]
                draw.polygon(points, fill=shield_color, outline='black')
                return image
            
            def notify_halt(self, message: str = None):
                """Flash red and show notification on HALT"""
                if self.icon:
                    self.halt_active = True
                    self.icon.icon = self.create_image("red")
                    
                    # Use custom message if provided, otherwise default
                    if message:
                        # Extract first sentence for title, rest for message body
                        parts = message.split(":", 1)
                        if len(parts) == 2:
                            title = parts[0].strip()
                            msg_body = parts[1].strip()
                        else:
                            title = "⚠️ Data Quality Alert"
                            msg_body = message
                    else:
                        title = "⚠️ Data Quality Alert"
                        msg_body = "Excel Guardian detected an issue. Click tray icon to review."
                    
                    self.icon.notify(title=title, message=msg_body)
            
            def reset(self):
                """Return to green state"""
                if self.icon:
                    self.halt_active = False
                    self.icon.icon = self.create_image("green")
            
            def setup(self, icon):
                """Setup callback when tray starts"""
                icon.visible = True
                icon.icon = self.create_image("green")
            
            def on_show_dashboard(self):
                """Open dashboard in browser (user opt-in)"""
                import webbrowser
                webbrowser.open(f"http://127.0.0.1:{self._api_port}")
            
            def on_exit(self, icon):
                """Exit the application"""
                icon.stop()
                # Don't sys.exit() here - let KeyboardInterrupt handle cleanup
            
            def run(self):
                """Run the tray icon"""
                menu = Menu(
                    MenuItem("Show Dashboard", self.on_show_dashboard),
                    MenuItem("Exit Guardian", self.on_exit)
                )
                
                self.icon = Icon(
                    name="Excel Guardian",
                    icon=self.create_image("green"),
                    title=f"Excel Guardian - Monitoring {self.manifest_name}",
                    menu=menu
                )
                self.icon.run(setup=self.setup)
        
        # Create and store wrapper
        wrapper = TrayIconWrapper(self.manifest.project_id)
        self.tray_icon = wrapper
        
        # Run tray icon in background thread
        tray_thread = Thread(target=wrapper.run, daemon=True)
        tray_thread.start()
        
        console.print("[green]✓[/green] System tray icon active (Silent Guardian mode)")
    
    def _get_severity_color(self, status: str) -> str:
        """Get Rich color for gate status"""
        if status == "HALT":
            return Theme.RED
        elif status == "PASS":
            return Theme.GREEN
        elif status == "WARN":
            return Theme.YELLOW
        else:
            return Theme.DIM
    
    def _create_header(self) -> Panel:
        """Create stunning ASCII art header matching dashboard theme"""
        # Modern ASCII art banner
        banner_lines = [
            "╔═══════════════════════════════════════════════════════════════════════════════════╗",
            "║                                                                                   ║",
            "║   ██████╗  ██████╗ ███████╗     ██████╗ ██╗   ██╗ █████╗ ██████╗ ██████╗         ║",
            "║   ██╔══██╗██╔══██╗██╔════╝    ██╔════╝ ██║   ██║██╔══██╗██╔══██╗██╔══██╗        ║",
            "║   ██║  ██║██████╔╝█████╗      ██║  ███╗██║   ██║███████║██████╔╝██║  ██║        ║",
            "║   ██║  ██║██╔══██╗██╔══╝      ██║   ██║██║   ██║██╔══██║██╔══██╗██║  ██║        ║",
            "║   ██████╔╝██║  ██║███████╗    ╚██████╔╝╚██████╔╝██║  ██║██║  ██║██████╔╝        ║",
            "║   ╚═════╝ ╚═╝  ╚═╝╚══════╝     ╚═════╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═════╝         ║",
            "║                                                                                   ║",
            "╚═══════════════════════════════════════════════════════════════════════════════════╝",
        ]
        
        # Build colored banner
        banner = Text()
        for i, line in enumerate(banner_lines):
            if i == 0 or i == len(banner_lines) - 1:
                banner.append(line + "\n", style=Theme.CYAN)
            elif "██" in line:
                # Color the DRE GUARD text in cyan, rest in dim
                banner.append(line + "\n", style=Theme.CYAN)
            else:
                banner.append(line + "\n", style=Theme.SUBTLE)
        
        # Status info line
        status_line = Text()
        status_line.append("  ⚡ ", style=Theme.YELLOW)
        status_line.append("Live Governance Monitor", style=Theme.HEADER)
        status_line.append("  │  ", style=Theme.SUBTLE)
        status_line.append(f"Project: ", style=Theme.SUBTLE)
        status_line.append(f"{self.manifest.project_id}", style=Theme.ACCENT)
        
        if self.enable_dashboard:
            status_line.append("  │  ", style=Theme.SUBTLE)
            status_line.append("Dashboard: ", style=Theme.SUBTLE)
            status_line.append(f"http://127.0.0.1:{self._api_port}", style=Theme.LINK)
        
        # Use Group instead of Text.assemble for mixed content
        from rich.console import Group
        content = Group(
            Align.center(banner),
            Align.center(status_line)
        )
        
        return Panel(
            content,
            box=box.SIMPLE,
            padding=(0, 0),
            style="on black"
        )
    
    def _create_status_bar(self) -> Panel:
        """Create stunning status bar with modern metrics display"""
        # Create individual metric cards
        status_color = Theme.RED if self.last_status == "HALT" else Theme.GREEN if self.last_status == "PASS" else Theme.YELLOW
        status_icon = "⛔" if self.last_status == "HALT" else "✓" if self.last_status == "PASS" else "⚠"
        
        # Build metrics table with styled cards
        table = Table.grid(padding=(0, 3), expand=True)
        table.add_column(justify="center")
        table.add_column(justify="center")
        table.add_column(justify="center")
        table.add_column(justify="center")
        
        # Status card
        status_text = Text()
        status_text.append(f"{status_icon} ", style=f"bold {status_color}")
        status_text.append(self.last_status or "READY", style=f"bold {status_color}")
        
        # Checks card
        checks_text = Text()
        checks_text.append("📊 ", style=Theme.CYAN)
        checks_text.append(f"{self.total_checks}", style=f"bold {Theme.WHITE}")
        checks_text.append(" checks", style=Theme.SUBTLE)
        
        # Halts card
        halt_color = Theme.RED if self.halt_count > 0 else Theme.GREEN
        halts_text = Text()
        halts_text.append("🚨 ", style=halt_color)
        halts_text.append(f"{self.halt_count}", style=f"bold {halt_color}")
        halts_text.append(" halts", style=Theme.SUBTLE)
        
        # Time card
        time_text = Text()
        time_text.append("🕐 ", style=Theme.CYAN)
        if self.last_check:
            time_text.append(self.last_check.strftime("%I:%M:%S %p"), style=Theme.WHITE)
        else:
            time_text.append("--:--:--", style=Theme.SUBTLE)
        
        table.add_row(
            Panel(status_text, box=box.ROUNDED, border_style=status_color, padding=(0, 2)),
            Panel(checks_text, box=box.ROUNDED, border_style=Theme.CYAN, padding=(0, 2)),
            Panel(halts_text, box=box.ROUNDED, border_style=halt_color, padding=(0, 2)),
            Panel(time_text, box=box.ROUNDED, border_style=Theme.CYAN, padding=(0, 2))
        )
        
        # Watching file indicator
        watch_text = Text()
        watch_text.append("👁 Watching: ", style=Theme.SUBTLE)
        watch_text.append(self.watching_file or "No file", style=Theme.CYAN)
        
        # Use a simple layout instead of Text.assemble with Align
        from rich.console import Group
        content = Group(
            Align.center(table),
            Align.center(watch_text)
        )
        
        return Panel(
            content,
            title=f"[bold {Theme.CYAN}]━━━ SYSTEM STATUS ━━━[/bold {Theme.CYAN}]",
            border_style=Theme.CYAN,
            box=box.DOUBLE,
            padding=(1, 2)
        )
    
    def _create_assertions_table(self) -> Panel:
        """Create live assertions table with human narratives - themed design"""
        
        if not self.current_assertions:
            empty_content = Text()
            empty_content.append("\n  ⏳ ", style=Theme.CYAN)
            empty_content.append("Waiting for first governance cycle...", style=Theme.SUBTLE)
            empty_content.append("\n")
            return Panel(
                empty_content,
                title=f"[bold {Theme.CYAN}]━━━ DATA QUALITY ALERTS ━━━[/bold {Theme.CYAN}]",
                border_style=Theme.CYAN,
                box=box.DOUBLE,
                padding=(1, 2)
            )
        
        # Show alerts in a more human-readable format
        content = Text()
        
        for assertion in self.current_assertions:
            gates = assertion.get("gate_status", {})
            gate_details = assertion.get("gate_details", {})
            name = assertion.get("logical_name", "Unknown")
            owner = assertion.get("owner_role", "Unknown")
            
            # Check each gate and generate narrative
            has_issues = False
            issues = []
            
            for gate_key, status in gates.items():
                if status == "HALT":
                    has_issues = True
                    gate_result = gate_details.get(gate_key, {})
                    
                    # Generate human narrative
                    gate_map = {"freshness": "gate_1", "stability": "gate_2", "alignment": "gate_4"}
                    gate_type = gate_map.get(gate_key, "gate_1")
                    narrative = self.brain.get_human_narrative(gate_type, gate_result, name)
                    
                    issues.append((narrative['title'], narrative['message'], narrative['action']))
            
            if has_issues:
                content.append("\n  ⛔ ", style=Theme.RED)
                content.append(name, style=f"bold {Theme.RED}")
                content.append(f"  ({owner})", style=Theme.YELLOW)
                content.append("\n")
                
                for title, message, action in issues:
                    content.append(f"     └─ {title}\n", style=Theme.ORANGE)
                    msg_display = message[:75] + "..." if len(message) > 75 else message
                    content.append(f"        {msg_display}\n", style=Theme.SUBTLE)
                    action_display = action[:70] + "..." if len(action) > 70 else action
                    content.append(f"        → {action_display}\n", style=Theme.CYAN)
            else:
                content.append("\n  ✓ ", style=Theme.GREEN)
                content.append(name, style=f"bold {Theme.GREEN}")
                content.append(f"  ({owner})", style=Theme.SUBTLE)
                content.append("  All checks passing\n", style=Theme.SUBTLE)
        
        border_color = Theme.RED if self.last_status == "HALT" else Theme.GREEN
        title_icon = "🚨" if self.last_status == "HALT" else "✅"
        
        return Panel(
            content if len(content) > 0 else Text("All assertions passing", style=Theme.GREEN),
            title=f"[bold {border_color}]━━━ {title_icon} DATA QUALITY ALERTS ━━━[/bold {border_color}]",
            border_style=border_color,
            box=box.DOUBLE,
            padding=(0, 2)
        )
    
    def _create_audit_log(self) -> Panel:
        """Create recent audit log panel with modern themed design"""
        audit_file = self.config.audit_log_path
        
        content = Text()
        
        if audit_file.exists():
            entries = []
            try:
                with open(audit_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            entries.append(json.loads(line))
            except Exception as e:
                content.append(f"Error: {str(e)}\n", style=Theme.RED)
            
            recent = entries[-6:] if len(entries) > 6 else entries
            recent.reverse()
            
            for entry in recent:
                # Parse ISO timestamp and convert to local time
                timestamp_str = entry.get('timestamp', '')
                if timestamp_str:
                    try:
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        local_dt = dt.astimezone()
                        timestamp = local_dt.strftime('%I:%M %p')
                    except Exception:
                        timestamp = 'N/A'
                else:
                    timestamp = 'N/A'
                    
                severity = entry.get('severity', 'INFO')
                
                # Severity icon and color
                if severity == "CRITICAL":
                    sev_icon, sev_color = "●", Theme.RED
                elif severity in ["WARN", "MAJOR"]:
                    sev_icon, sev_color = "●", Theme.YELLOW
                else:
                    sev_icon, sev_color = "●", Theme.GREEN
                
                # Extract narrative if available
                details = entry.get('details', {})
                if 'narratives' in details and details['narratives']:
                    narrative_text = details['narratives'][0].get('title', 'Alert')
                elif 'narrative' in details:
                    narrative_text = details['narrative'].get('title', 'Alert')
                else:
                    narrative_text = entry.get('event_type', 'UNKNOWN')
                
                # Truncate narrative
                narrative_display = narrative_text[:35] + "..." if len(narrative_text) > 35 else narrative_text
                
                content.append(f"\n  {sev_icon} ", style=sev_color)
                content.append(f"{timestamp}", style=Theme.SUBTLE)
                content.append(f"\n    {narrative_display}\n", style=Theme.WHITE)
        else:
            content.append("\n  📋 No audit events yet\n", style=Theme.SUBTLE)
        
        return Panel(
            content,
            title=f"[bold {Theme.PURPLE}]━━━ 📜 ACTIVITY LOG ━━━[/bold {Theme.PURPLE}]",
            border_style=Theme.PURPLE,
            box=box.DOUBLE,
            padding=(0, 1)
        )
    
    def _create_layout(self) -> Layout:
        """Create stunning terminal layout with themed design"""
        layout = Layout()
        
        layout.split(
            Layout(name="header", size=15),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=4)
        )
        
        layout["body"].split_row(
            Layout(name="main", ratio=3),
            Layout(name="sidebar", ratio=1, minimum_size=35)
        )
        
        layout["main"].split(
            Layout(name="status", size=9),
            Layout(name="assertions", ratio=1, minimum_size=15)
        )
        
        layout["header"].update(self._create_header())
        layout["status"].update(self._create_status_bar())
        layout["assertions"].update(self._create_assertions_table())
        layout["sidebar"].update(self._create_audit_log())
        
        # Create themed footer
        footer_text = Text()
        footer_text.append("  ⌨ ", style=Theme.CYAN)
        footer_text.append("Ctrl+C", style=f"bold {Theme.WHITE}")
        footer_text.append(" to exit  │  ", style=Theme.SUBTLE)
        footer_text.append("🌐 ", style=Theme.CYAN)
        footer_text.append(f"http://127.0.0.1:{self._api_port}", style=Theme.LINK)
        footer_text.append("  │  ", style=Theme.SUBTLE)
        footer_text.append("📁 ", style=Theme.GREEN)
        footer_text.append("File changes trigger automatic checks", style=Theme.SUBTLE)
        
        layout["footer"].update(
            Panel(
                Align.center(footer_text),
                box=box.SIMPLE,
                style=f"on black",
                padding=(0, 0)
            )
        )
        
        return layout
    
    def run_governance_cycle(self, filepath=None):
        """Execute governance cycle and update UI"""
        try:
            # Load current state
            ingestor = ExcelIngestor(self.manifest, self.manifest_path)
            current_state = ingestor.read_data()
            
            global_halt = False
            report = []
            conflict_results = []  # Store Gate 3 results
            
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
                    
                    # Generate human narratives for all gates
                    narratives = []
                    if g1["status"] == "HALT":
                        narratives.append(self.brain.get_human_narrative("gate_1", g1, assertion.logical_name))
                    if g2["status"] == "HALT":
                        narratives.append(self.brain.get_human_narrative("gate_2", g2, assertion.logical_name))
                    if g4["status"] == "HALT":
                        narratives.append(self.brain.get_human_narrative("gate_4", g4, assertion.logical_name))
                    
                    # Log to audit with both technical and human-friendly data
                    self.audit_logger.log_event(
                        event_type="HALT",
                        assertion_id=assertion.id,
                        details={
                            "technical": {
                                "gate_1_freshness": g1,
                                "gate_2_stability": g2,
                                "gate_4_structure": g4
                            },
                            "narratives": narratives
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
            
            # Gate 3: Convergence Check (Conflict Pair Analysis)
            if self.manifest.conflict_pairs:
                for id1, id2 in self.manifest.conflict_pairs:
                    # Find assertions by ID
                    assertion1 = next((a for a in self.manifest.assertions if a.id == id1), None)
                    assertion2 = next((a for a in self.manifest.assertions if a.id == id2), None)
                    
                    if assertion1 and assertion2:
                        g3 = self.brain.gate_3_convergence(assertion1, assertion2)
                        
                        # Check for HALT
                        if g3["status"] == "HALT":
                            global_halt = True
                            
                            # Generate human narrative for conflict
                            narrative = self.brain.get_human_narrative("gate_3", g3, f"{assertion1.logical_name} vs {assertion2.logical_name}")
                            
                            # Log to audit with overlap integral and narrative
                            self.audit_logger.log_event(
                                event_type="GATE_3_CONFLICT",
                                assertion_id=f"{id1}+{id2}",
                                details={
                                    "technical": {
                                        "gate_3_convergence": g3,
                                        "overlap_integral": g3["overlap_integral"],
                                        "assertion1": g3["assertion1"],
                                        "assertion2": g3["assertion2"]
                                    },
                                    "narrative": narrative
                                },
                                user=f"{assertion1.owner_role}+{assertion2.owner_role}",
                                severity=g3["severity"]
                            )
                        
                        conflict_results.append(g3)
            
            # Update state
            self.last_check = datetime.now()
            self.total_checks += 1
            self.last_status = "HALT" if global_halt else "PASS"
            if global_halt:
                self.halt_count += 1
            self.current_assertions = report
            
            # Push state to dashboard via shared memory (same process)
            # This is the "Push" model - no HTTP polling needed
            try:
                import guardian.api.bridge as bridge_module
                import asyncio
                
                governance_state = {
                    "status": self.last_status,
                    "assertions": report,
                    "conflict_pair": conflict_results[0] if conflict_results else None,
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                    "project_name": self.manifest.project_id,
                    "total_assertions": len(self.manifest.assertions)
                }
                
                # Update shared state (direct memory access, no HTTP)
                bridge_module.current_governance_state = governance_state
                
                # Push to all WebSocket clients (async broadcast)
                if bridge_module.manager.active_connections:
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(bridge_module.manager.broadcast(governance_state))
                        else:
                            loop.run_until_complete(bridge_module.manager.broadcast(governance_state))
                    except RuntimeError:
                        # No event loop - create one for broadcast
                        asyncio.run(bridge_module.manager.broadcast(governance_state))
                
                logger.debug(f"State pushed to {len(bridge_module.manager.active_connections)} clients")
                
            except Exception as e:
                logger.error(f"Failed to push state: {e}")
            
            # Notify system tray on HALT (no browser hijack)
            if global_halt and hasattr(self, 'tray_icon'):
                # Generate human-friendly notification message
                halt_message = None
                for assertion_report in report:
                    gate_details = assertion_report.get("gate_details", {})
                    assertion_name = assertion_report.get("logical_name", "Unknown")
                    
                    # Check each gate for HALT
                    for gate_key in ["freshness", "stability", "alignment"]:
                        if gate_key in gate_details and gate_details[gate_key].get("status") == "HALT":
                            gate_map = {"freshness": "gate_1", "stability": "gate_2", "alignment": "gate_4"}
                            narrative = self.brain.get_human_narrative(
                                gate_map[gate_key],
                                gate_details[gate_key],
                                assertion_name
                            )
                            halt_message = f"{narrative['title']}: {narrative['message']}"
                            break
                    
                    if halt_message:
                        break
                
                # Check conflict results for Gate 3 narratives
                if not halt_message and conflict_results:
                    for g3_result in conflict_results:
                        if g3_result.get("status") == "HALT":
                            a1_name = g3_result["assertion1"]["logical_name"]
                            a2_name = g3_result["assertion2"]["logical_name"]
                            narrative = self.brain.get_human_narrative(
                                "gate_3",
                                g3_result,
                                f"{a1_name} vs {a2_name}"
                            )
                            halt_message = f"{narrative['title']}: {narrative['message']}"
                            break
                
                if halt_message and self.tray_icon:
                    try:
                        self.tray_icon.notify_halt(halt_message)
                    except:
                        pass
        
        except Exception as e:
            # Show full error message, not truncated
            error_msg = str(e)
            self.last_status = f"ERROR: {error_msg}"
            logger.error(f"Governance cycle failed: {error_msg}", exc_info=True)
    
    def start_monitoring(self, watch_path: str = None):
        """Start live monitoring with file watcher"""
        # Resolve watch path to directory containing manifest
        if watch_path is None:
            # Use the directory where the manifest.json is located
            manifest_dir = Path(self.manifest_path).parent
            watch_path = str(manifest_dir)
        
        self.watching_file = f"{watch_path}/{self.manifest.target_file}"
        
        # Register this monitor instance with Bridge for command ingress
        if self.enable_dashboard:
            import guardian.api.bridge as bridge_module
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
        
        # Display monitoring started confirmation - cleaner output
        target_filename = Path(self.manifest.target_file).name
        console.clear()
        
        # Print dashboard link prominently if enabled
        if self.enable_dashboard:
            console.print()
            console.print(f"  [bold {Theme.CYAN}]━━━ DASHBOARD ━━━[/bold {Theme.CYAN}]")
            console.print(f"  [bold {Theme.GREEN}]✓[/bold {Theme.GREEN}] Dashboard running at: [bold underline {Theme.CYAN}]http://127.0.0.1:{self._api_port}[/bold underline {Theme.CYAN}]")
            console.print()
        
        # Static display - print once, update only on state changes
        try:
            last_state = None
            
            # Print initial layout
            console.print(self._create_layout())
            last_state = (self.last_status, self.total_checks, self.halt_count, len(self.current_assertions))
            
            # Monitor loop - only reprint when state actually changes
            while True:
                time.sleep(1)
                current_state = (self.last_status, self.total_checks, self.halt_count, len(self.current_assertions))
                
                # Only update display if state actually changed (not time-based)
                if current_state != last_state:
                    console.clear()
                    if self.enable_dashboard:
                        console.print()
                        console.print(f"  [bold {Theme.CYAN}]━━━ DASHBOARD ━━━[/bold {Theme.CYAN}]")
                        console.print(f"  [bold {Theme.GREEN}]✓[/bold {Theme.GREEN}] Dashboard running at: [bold underline {Theme.CYAN}]http://127.0.0.1:{self._api_port}[/bold underline {Theme.CYAN}]")
                        console.print()
                    console.print(self._create_layout())
                    last_state = current_state
                    
        except KeyboardInterrupt:
            observer.stop()
            observer.join()
            
            # Cleanup uvicorn subprocess
            if self._api_process:
                try:
                    if sys.platform == "win32":
                        subprocess.run(["taskkill", "/F", "/T", "/PID", str(self._api_process.pid)],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        self._api_process.terminate()
                        self._api_process.wait(timeout=2)
                except:
                    pass
            
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
            
            console.print("\n[green]✓ Monitoring stopped gracefully[/green]")


if __name__ == "__main__":
    import sys
    
    # Parse args
    enable_dashboard = "--dashboard" in sys.argv or "-d" in sys.argv
    
    try:
        # Initialize config
        config = get_config()
        manifest_path = str(config.manifest_path)
    except Exception as e:
        error_msg = f"Failed to initialize: {e}\\n\\nPlease ensure manifest.json exists in project_space/"
        
        # Show message box on Windows if running as frozen executable
        if getattr(sys, 'frozen', False) and sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "DRE Guardian - Initialization Error", 0x10)
            except:
                pass
        
        console.print(f"[{Theme.RED}]✗ Error:[/{Theme.RED}] {error_msg}")
        sys.exit(1)
    
    # Startup Banner - themed to match the CLI
    console.clear()
    startup_text = Text()
    startup_text.append("\n")
    startup_text.append("  ╔═══════════════════════════════════════════════════════════════╗\n", style=Theme.CYAN)
    startup_text.append("  ║                                                               ║\n", style=Theme.CYAN)
    startup_text.append("  ║   ", style=Theme.CYAN)
    startup_text.append("⚡ DRE GUARDIAN", style=f"bold {Theme.WHITE}")
    startup_text.append(" - Data Reliability Engine", style=Theme.SUBTLE)
    startup_text.append("         ║\n", style=Theme.CYAN)
    startup_text.append("  ║                                                               ║\n", style=Theme.CYAN)
    startup_text.append("  ╚═══════════════════════════════════════════════════════════════╝\n", style=Theme.CYAN)
    console.print(startup_text)
    
    if enable_dashboard:
        console.print(f"  [{Theme.GREEN}]✓[/{Theme.GREEN}] Dashboard will be served on port 8000-8002")
        console.print(f"  [{Theme.YELLOW}]ℹ[/{Theme.YELLOW}] Dashboard does not auto-open. Access from the monitor display.\n")
    
    console.print(f"  [{Theme.SUBTLE}]Loading manifest...[/{Theme.SUBTLE}]\n")
    
    try:
        monitor = DREMonitor(manifest_path, enable_dashboard=enable_dashboard)
        monitor.start_monitoring()
    except FileNotFoundError as e:
        error_msg = f"Manifest not found: {e}\\n\\nRun 'dre init' to create a new project."
        
        if getattr(sys, 'frozen', False) and sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "DRE Guardian - File Not Found", 0x10)
            except:
                pass
        
        console.print(f"[{Theme.RED}]✗ Manifest not found. Run:[/{Theme.RED}] [{Theme.CYAN}]dre init[/{Theme.CYAN}]")
        sys.exit(1)
    except Exception as e:
        error_msg = f"Monitor startup failed: {e}"
        
        if getattr(sys, 'frozen', False) and sys.platform == 'win32':
            try:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, error_msg, "DRE Guardian Error", 0x10)
            except:
                pass
        
        console.print(f"[{Theme.RED}]✗ Error:[/{Theme.RED}] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
