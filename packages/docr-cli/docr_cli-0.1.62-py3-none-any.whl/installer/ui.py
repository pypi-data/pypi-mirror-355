"""UI and display functions for the installation process."""

import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Confirm
from rich import box
from utils import AppConfig
from utils.shared_console import get_shared_console


class InstallUI:
    """Handle all UI display for the installation process."""
    
    def __init__(self):
        self.console = get_shared_console()
        
    def show_banner(self):
        """Display welcome banner."""
        initials = AppConfig.get_developer_initials()
        # Check if using override
        override_source = " (overridden)" if os.environ.get('DOCR_OVERRIDE_INITIALS') else " (from config)"
        
        banner = Panel(
            "[bold cyan]Document Review System[/bold cyan]\n"
            "[dim]Automated Installation Tool[/dim]\n\n"
            f"Developer: [yellow]{initials}{override_source}[/yellow]",
            title="[bold]🚀 Doc Review Installer[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
        self.console.print(banner)
    
    def show_override_warning(self):
        """Show warning if using override initials different from config."""
        override = os.environ.get('DOCR_OVERRIDE_INITIALS')
        if override:
            # Get stored initials directly from config
            try:
                from utils import ProjectConfig
                config_data = AppConfig.load_config()
                stored_initials = ProjectConfig(config_data).get_developer_initials()
                
                if override != stored_initials:
                    self.console.print(Panel(
                        f"⚠️  Using override initials '[yellow]{override}[/yellow]' instead of configured '[cyan]{stored_initials}[/cyan]'\n"
                        "All resources will be deployed with the override initials.",
                        title="[yellow]Developer Initials Override[/yellow]",
                        border_style="yellow",
                        padding=(1, 2)
                    ))
                    self.console.print()  # Add spacing
            except Exception:
                # If we can't get stored initials, just continue
                pass
        
    def show_setup_error(self):
        """Display setup error with nice formatting."""
        error_panel = Panel(
            "[red]Setup has not been completed![/red]\n\n"
            "Please run '[yellow]docr setup[/yellow]' first to configure your environment.\n"
            "This will set up your initials and create the necessary configuration.",
            title="[red]❌ Configuration Error[/red]",
            border_style="red",
            padding=(1, 2)
        )
        self.console.print(error_panel)
        
    def show_installation_plan(self, steps: List[Dict], skip_frontend: bool, resume_from: Optional[int]) -> bool:
        """Display installation plan and get confirmation."""
        # Create installation plan table
        table = Table(
            title="\n[bold]Installation Plan[/bold]",
            box=box.ROUNDED,
            title_style="bold blue"
        )
        
        table.add_column("Step", style="cyan", width=4)
        table.add_column("Component", style="yellow")
        table.add_column("Action", style="white")
        table.add_column("Type", style="magenta")
        
        step_offset = resume_from - 1 if resume_from else 0
        
        for i, step in enumerate(steps, start=1):
            step_num = i + step_offset
            step_type = self._get_step_type(step)
            table.add_row(
                str(step_num),
                step['name'],
                step['description'],
                step_type
            )
        
        self.console.print(table)
        
        # Show summary
        total_steps = len(steps)
        backend_steps = sum(1 for s in steps if 'frontend' not in s['name'].lower())
        frontend_steps = total_steps - backend_steps
        
        summary = Panel(
            f"Total steps: [cyan]{total_steps}[/cyan]\n"
            f"Backend deployments: [yellow]{backend_steps}[/yellow]\n"
            f"Frontend deployments: [green]{frontend_steps}[/green]\n"
            f"Estimated time: [magenta]~{self._estimate_time(skip_frontend)}[/magenta]",
            title="[bold]Summary[/bold]",
            border_style="blue"
        )
        self.console.print(summary)
        
        # Confirm
        if not Confirm.ask("\n[bold]Proceed with installation?[/bold]", default=True):
            self.console.print("[yellow]Installation cancelled.[/yellow]")
            return False
            
        return True
    
    def list_steps(self, steps: List[Dict], skip_frontend: bool):
        """Display just the steps without confirmation prompt."""
        # Create installation plan table
        table = Table(
            title="\n[bold]Installation Steps[/bold]",
            box=box.ROUNDED,
            title_style="bold blue"
        )
        
        table.add_column("Step", style="cyan", width=4)
        table.add_column("Component", style="yellow")
        table.add_column("Action", style="white")
        table.add_column("Type", style="magenta")
        
        for i, step in enumerate(steps, start=1):
            step_type = self._get_step_type(step)
            table.add_row(
                str(i),
                step['name'],
                step['description'],
                step_type
            )
        
        self.console.print(table)
        
        # Show summary
        total_steps = len(steps)
        backend_steps = sum(1 for s in steps if 'frontend' not in s['name'].lower())
        frontend_steps = total_steps - backend_steps
        
        summary = Panel(
            f"Total steps: [cyan]{total_steps}[/cyan]\n"
            f"Backend deployments: [yellow]{backend_steps}[/yellow]\n"
            f"Frontend deployments: [green]{frontend_steps}[/green]\n"
            f"Estimated time: [magenta]~{self._estimate_time(skip_frontend)}[/magenta]",
            title="[bold]Summary[/bold]",
            border_style="blue"
        )
        self.console.print(summary)
        
    def show_step_start(self, step_num: int, step: Dict, total_steps: int):
        """Show step starting panel."""
        panel = Panel(
            f"[bold]{step['description']}[/bold]\n"
            f"Step {step_num} of {total_steps}",
            title=f"[bold blue]🔄 {step['name']}[/bold blue]",
            border_style="blue"
        )
        self.console.print(panel)
        
    def show_step_complete(self, step_num: int, step: Dict):
        """Show step completion."""
        self.console.print(f"[green]✅ Step {step_num} completed successfully![/green]\n")
        
    def show_step_failed(self, step_num: int, step: Dict, error: str, log_file: Path):
        """Show step failure."""
        error_panel = Panel(
            f"[red]{error}[/red]\n\n"
            f"Check log file for details: {log_file}",
            title=f"[red]❌ Step {step_num} Failed: {step['name']}[/red]",
            border_style="red"
        )
        self.console.print(error_panel)
        
    def show_log_location(self, log_file: Path, log_dir: Path):
        """Show log file location."""
        self.console.print(Panel(
            f"📝 Installation log: {log_file}\n"
            f"📁 Progress tracking: {log_dir}",
            title="[bold blue]Log Files[/bold blue]",
            border_style="blue"
        ))
    
    def prompt_continue(self) -> bool:
        """Prompt user to continue with installation."""
        return Confirm.ask("\n[bold cyan]Ready to proceed with installation?[/bold cyan]", default=True)
        
    def show_summary(self, success: bool, completed_steps: int, failed_steps: int, 
                     elapsed: str, log_file: Path, last_step_num: int):
        """Show installation summary."""
        if success:
            # Get the frontend URLs from the config
            try:
                config = AppConfig.load_config()
                oidc_url = None
                lr_url = None
                
                # Get CloudFront URLs
                if 'applications' in config:
                    if 'oidc-manager' in config['applications']:
                        oidc_url = config['applications']['oidc-manager'].get('stage_sandbox_frontend_url')
                    if 'legislative-review' in config['applications']:
                        lr_url = config['applications']['legislative-review'].get('stage_sandbox_frontend_url')
                
                # Success summary
                self.console.print("\n")
                summary = Panel(
                    f"[green]✨ Installation completed successfully![/green]\n\n"
                    f"Total time: [cyan]{elapsed}[/cyan]\n"
                    f"Completed steps: [green]{completed_steps}[/green]\n"
                    f"Log file: {log_file}",
                    title="[bold green]🎉 Installation Complete[/bold green]",
                    border_style="green",
                    padding=(1, 2)
                )
                self.console.print(summary)
                
                # Show web URLs
                self.console.print("\n[bold cyan]🌐 Web Applications:[/bold cyan]\n")
                
                if oidc_url:
                    self.console.print(f"  OIDC Manager:        [link={oidc_url}]{oidc_url}[/link]")
                else:
                    self.console.print(f"  OIDC Manager:        [yellow]URL not found - run 'docr refresh'[/yellow]")
                    
                if lr_url:
                    self.console.print(f"  Legislative Review:  [link={lr_url}]{lr_url}[/link]")
                else:
                    self.console.print(f"  Legislative Review:  [yellow]URL not found - run 'docr refresh'[/yellow]")
                
                # Show next steps
                self.console.print("\n[bold cyan]📋 Next Steps:[/bold cyan]\n")
                self.console.print("1. Add yourself to the following groups at [link=https://grouper.dev.umd.edu/]https://grouper.dev.umd.edu/[/link]:\n")
                self.console.print("   [yellow]Required groups:[/yellow]")
                self.console.print("   • Application Roles : Division of Information Technology : OIDC : oidcadmin : admins")
                self.console.print("   • Application Roles : Division of Information Technology : OIDC : aisolutions : docreview : legislative-review : admins")
                self.console.print("   • Application Roles : Division of Information Technology : OIDC : aisolutions : docreview : legislative-review : costs")
                self.console.print("   • Application Roles : Division of Information Technology : OIDC : aisolutions : docreview : legislative-review : jobs")
                self.console.print("   • Application Roles : Division of Information Technology : OIDC : aisolutions : docreview : legislative-review : marylandworkspace")
                
                self.console.print("\n2. Login to OIDC Manager and verify access")
                self.console.print("3. Login to Legislative Review, select 'Maryland Workspace' from dropdown, and verify you see bills")
                
                self.console.print("\n[bold cyan]🛠️  Useful Commands:[/bold cyan]\n")
                self.console.print("  • View system status:    [cyan]docr doctor all[/cyan]")
                self.console.print("  • Check OIDC setup:      [cyan]docr doctor oidc[/cyan]")
                self.console.print("  • Fast backend deploy:   [cyan]docr deploy backend <app-name>[/cyan]")
                self.console.print("  • Deploy frontend:       [cyan]docr deploy frontend[/cyan]")
                
            except Exception:
                # If we can't get URLs, show the basic summary
                self.console.print(summary)
                
        else:
            # Failure summary
            summary = Panel(
                f"[red]Installation failed[/red]\n\n"
                f"Total time: [cyan]{elapsed}[/cyan]\n"
                f"Completed steps: [green]{completed_steps}[/green]\n"
                f"Failed steps: [red]{failed_steps}[/red]\n"
                f"Log file: {log_file}\n\n"
                f"[yellow]To resume installation:[/yellow]\n"
                f"docr install --resume-from {last_step_num + 1}",
                title="[bold red]❌ Installation Failed[/bold red]",
                border_style="red",
                padding=(1, 2)
            )
            
            self.console.print("\n")
            self.console.print(summary)
            
    def _get_step_type(self, step: Dict) -> str:
        """Determine the type of step for display."""
        name = step['name'].lower()
        if 'deploy' in name:
            if 'frontend' in name:
                return "🌐 Frontend"
            elif 'component' in name:
                return "📦 Component"
            elif 'application' in name:
                return "🔧 Application"
            else:
                return "🏗️  Deploy"
        elif 'config' in name:
            return "⚙️  Config"
        elif 'refresh' in name:
            return "🔄 Refresh"
        elif 'register' in name:
            return "🔐 OIDC"
        elif 'bootstrap' in name:
            return "📊 Data"
        elif 'job' in name:
            return "👷 Job"
        else:
            return "📋 Task"
            
    def _estimate_time(self, skip_frontend: bool) -> str:
        """Estimate total installation time."""
        if skip_frontend:
            return "30-40 minutes"
        else:
            return "50-65 minutes"