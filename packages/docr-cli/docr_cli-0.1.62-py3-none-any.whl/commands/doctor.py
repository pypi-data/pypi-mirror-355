#!/usr/bin/env python3
"""Doctor command for system health checks."""

import typer
from typing import Optional
from utils import ConsoleUtils, AppConfig
from doctor.stacks import StackDoctor
from doctor.config import ConfigDoctor
from doctor.oidc import OIDCDoctor
from doctor.cleanup import CleanupDoctor

app = typer.Typer(help="System health checks and diagnostics")


@app.command()
def stacks(
    stage: str = typer.Option("sandbox", help="Target stage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Verify CloudFormation stack deployments."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    console_utils = ConsoleUtils()
    
    # Enhanced header with better styling
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    
    # Create header content
    header_text = Text()
    header_text.append("📚 ", style="")
    header_text.append("Stack Verification", style="bold green")
    header_text.append(f" [{stage}]", style="dim")
    if fix:
        header_text.append(" 🔧", style="blue")
    
    # Create stylized header panel
    header_panel = Panel(
        Align.center(header_text),
        style="green",
        padding=(1, 2)
    )
    
    console_utils.console.print(header_panel)
    console_utils.console.print()
    
    doctor = StackDoctor(stage=stage, verbose=verbose, fix=fix)
    success = doctor.check()
    doctor.print_summary("Stack Verification")
    
    if not success:
        raise typer.Exit(1)


@app.command()
def config(
    stage: str = typer.Option("sandbox", help="Target stage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Verify backend and frontend configuration files."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    console_utils = ConsoleUtils()
    
    # Enhanced header with better styling
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    
    # Create header content
    header_text = Text()
    header_text.append("⚙️ ", style="")
    header_text.append("Configuration Verification", style="bold yellow")
    header_text.append(f" [{stage}]", style="dim")
    if fix:
        header_text.append(" 🔧", style="blue")
    
    # Create stylized header panel
    header_panel = Panel(
        Align.center(header_text),
        style="yellow",
        padding=(1, 2)
    )
    
    console_utils.console.print(header_panel)
    console_utils.console.print()
    
    doctor = ConfigDoctor(stage=stage, verbose=verbose, fix=fix)
    success = doctor.check()
    doctor.print_summary("Configuration Verification")
    
    if not success:
        raise typer.Exit(1)


@app.command()
def oidc(
    stage: str = typer.Option("sandbox", help="Target stage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Verify OIDC client registrations and authentication setup."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    console_utils = ConsoleUtils()
    
    # Enhanced header with better styling
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    
    # Create header content
    header_text = Text()
    header_text.append("🩺 ", style="")
    header_text.append("OIDC System Health Check", style="bold cyan")
    header_text.append(f" [{stage}]", style="dim")
    
    # Create stylized header panel
    header_panel = Panel(
        Align.center(header_text),
        style="cyan",
        padding=(1, 2)
    )
    
    console_utils.console.print(header_panel)
    console_utils.console.print()
    
    doctor = OIDCDoctor(stage=stage, verbose=verbose)
    success = doctor.check()
    doctor.print_summary("OIDC Verification")
    
    if not success:
        raise typer.Exit(1)


@app.command()
def clean(
    stage: str = typer.Option("sandbox", help="Target stage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Clean up orphaned resources and invalid configurations."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    console_utils = ConsoleUtils()
    
    if not confirm:
        console_utils.print_warning("This will clean up orphaned resources and configurations.")
        if not typer.confirm("Continue?"):
            console_utils.print_info("Cleanup cancelled")
            return
    
    # Enhanced header with better styling
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    
    # Create header content
    header_text = Text()
    header_text.append("🧹 ", style="")
    header_text.append("System Cleanup", style="bold red")
    header_text.append(f" [{stage}]", style="dim")
    
    # Create stylized header panel
    header_panel = Panel(
        Align.center(header_text),
        style="red",
        padding=(1, 2)
    )
    
    console_utils.console.print(header_panel)
    console_utils.console.print()
    
    doctor = CleanupDoctor(stage=stage, verbose=verbose, fix=True)
    doctor.check()
    doctor.print_summary("System Cleanup")


@app.command()
def all(
    stage: str = typer.Option("sandbox", help="Target stage"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix issues"),
    parallel: bool = typer.Option(True, "--parallel/--sequential", help="Run checks in parallel"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Run all verification checks."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    console_utils = ConsoleUtils()
    
    # Enhanced header for full system check
    from rich.panel import Panel
    from rich.text import Text
    from rich.align import Align
    
    # Create header content
    header_text = Text()
    header_text.append("🩺 ", style="")
    header_text.append("Complete System Health Check", style="bold magenta")
    header_text.append(f" [{stage}]", style="dim")
    if fix:
        header_text.append(" 🔧", style="blue")
    
    # Create stylized header panel
    header_panel = Panel(
        Align.center(header_text),
        style="magenta",
        padding=(1, 2)
    )
    
    console_utils.console.print(header_panel)
    console_utils.console.print()
    
    checks = [
        ("Stacks", StackDoctor),
        ("Configuration", ConfigDoctor),
        ("OIDC", OIDCDoctor)
    ]
    
    overall_success = True
    failed_checks = []
    
    for i, (check_name, doctor_class) in enumerate(checks, 1):
        # Enhanced section header
        section_text = Text()
        section_text.append(f"🔍 [{i}/{len(checks)}] ", style="dim")
        section_text.append(f"{check_name} Verification", style="bold blue")
        
        console_utils.console.print()
        console_utils.console.print(section_text)
        console_utils.console.print("─" * 40, style="dim")
        
        # Skip fix for OIDC as it doesn't support it yet
        check_fix = fix if doctor_class != OIDCDoctor else False
        
        doctor = doctor_class(stage=stage, verbose=verbose, fix=check_fix)
        success = doctor.check()
        doctor.print_summary(f"{check_name} Verification")
        
        if not success:
            overall_success = False
            # Collect failed checks from this doctor
            for detail in doctor.results['details']:
                if not detail['passed']:
                    failed_checks.append({
                        'category': check_name,
                        'check': detail['check'],
                        'message': detail['message']
                    })
    
    # Enhanced overall summary
    from rich.panel import Panel
    console_utils.console.print()
    
    if overall_success:
        summary_text = Text()
        summary_text.append("✅ All system health checks passed!", style="bold green")
        
        summary_panel = Panel(
            Align.center(summary_text),
            title="[bold]Final Result[/bold]",
            border_style="green",
            padding=(1, 2)
        )
        console_utils.console.print(summary_panel)
    else:
        # Show ERROR panel
        error_text = Text()
        error_text.append("❌ SYSTEM HEALTH CHECK FAILED", style="bold red")
        
        error_panel = Panel(
            Align.center(error_text),
            title="[bold red]ERROR[/bold red]",
            border_style="red",
            padding=(1, 2)
        )
        console_utils.console.print(error_panel)
        
        # List all failed checks
        if failed_checks:
            console_utils.console.print("\n[bold red]Failed Checks:[/bold red]")
            for failed in failed_checks:
                console_utils.console.print(f"  ❌ [{failed['category']}] {failed['check']}")
                if '\n' in failed['message']:
                    # Multi-line messages (like OIDC table error)
                    for line in failed['message'].split('\n'):
                        console_utils.console.print(f"     {line.strip()}", style="dim red")
                else:
                    console_utils.console.print(f"     {failed['message']}", style="dim red")
        
    if not overall_success:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()