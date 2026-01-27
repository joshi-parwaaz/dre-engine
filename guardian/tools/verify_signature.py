"""
Digital Signature Verification Tool

Verifies SHA-256 hashes in the audit log for non-repudiation.
This tool can be used to prove that an override justification hasn't been tampered with.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich import box

console = Console()


def compute_hash(justification: str, signature: str, timestamp: str) -> str:
    """
    Compute SHA-256 hash from override components.
    Must match the frontend algorithm exactly.
    """
    hash_input = f"{justification}|{signature}|{timestamp}"
    return hashlib.sha256(hash_input.encode()).hexdigest()


def verify_audit_log(audit_log_path: str = None):
    """
    Verify all override signatures in the audit log.
    """
    if audit_log_path is None:
        project_root = Path(__file__).parent.parent.parent
        audit_log_path = str(project_root / "project_space" / "audit_log.jsonl")
    
    console.print("\n[bold cyan]🔐 Digital Signature Verification[/bold cyan]\n")
    console.print(f"[dim]Audit log: {audit_log_path}[/dim]\n")
    
    if not Path(audit_log_path).exists():
        console.print("[red]✗ Audit log not found[/red]")
        return
    
    overrides = []
    with open(audit_log_path, 'r') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get("event_type") == "OVERRIDE_REQUEST":
                overrides.append(entry)
    
    if not overrides:
        console.print("[yellow]No override requests found in audit log[/yellow]")
        return
    
    console.print(f"[cyan]Found {len(overrides)} override(s) to verify[/cyan]\n")
    
    table = Table(title="Override Signature Verification", box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan", width=20)
    table.add_column("User", style="yellow", width=20)
    table.add_column("Assertion", style="white", width=15)
    table.add_column("Stored Hash", style="magenta", width=20)
    table.add_column("Verification", justify="center", width=12)
    
    verified_count = 0
    failed_count = 0
    
    for entry in overrides:
        details = entry.get("details", {})
        stored_hash = details.get("signature_hash", "")
        
        # Get override components
        justification = details.get("justification", "")
        user = entry.get("user", "")
        timestamp = details.get("timestamp", "")
        
        # Recompute hash
        if justification and user and timestamp:
            computed_hash = compute_hash(justification, user, timestamp)
            
            # Verify
            if computed_hash == stored_hash:
                verification = "[green]✓ VALID[/green]"
                verified_count += 1
            else:
                verification = "[red]✗ TAMPERED[/red]"
                failed_count += 1
        else:
            verification = "[yellow]? INCOMPLETE[/yellow]"
            failed_count += 1
        
        table.add_row(
            timestamp[:19] if timestamp else "N/A",
            user[:20] if user else "N/A",
            entry.get("assertion_id", "N/A")[:15],
            stored_hash[:16] + "..." if stored_hash else "N/A",
            verification
        )
    
    console.print(table)
    console.print()
    
    # Summary
    if failed_count == 0:
        console.print(f"[bold green]✓ All {verified_count} override signature(s) verified successfully[/bold green]")
        console.print("[dim]No tampering detected - audit trail integrity maintained[/dim]\n")
    else:
        console.print(f"[bold red]⚠ WARNING: {failed_count} signature(s) failed verification![/bold red]")
        console.print("[dim]Possible tampering or data corruption detected[/dim]\n")


def verify_single_override(justification: str, signature: str, timestamp: str, stored_hash: str):
    """
    Verify a single override signature.
    """
    console.print("\n[bold cyan]🔐 Single Override Verification[/bold cyan]\n")
    
    computed_hash = compute_hash(justification, signature, timestamp)
    
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
        return True
    else:
        console.print("[bold red]✗ SIGNATURE INVALID[/bold red]")
        console.print("[dim]Override may have been tampered with or data is corrupt[/dim]\n")
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Manual verification mode
        if len(sys.argv) != 5:
            console.print("[red]Usage: python verify_signature.py <justification> <signature> <timestamp> <stored_hash>[/red]")
            console.print("[dim]Or run without arguments to verify entire audit log[/dim]")
            sys.exit(1)
        
        verify_single_override(
            justification=sys.argv[1],
            signature=sys.argv[2],
            timestamp=sys.argv[3],
            stored_hash=sys.argv[4]
        )
    else:
        # Verify entire audit log
        verify_audit_log()
