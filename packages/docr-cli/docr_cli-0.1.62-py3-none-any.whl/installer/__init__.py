"""Install command module for Document Review CLI."""

import os
import time
import json
from typing import Optional, List, Dict
from pathlib import Path
from datetime import datetime
from rich.table import Table
from rich import box
import typer
from utils.base_cli import BaseCLI
from utils import AppConfig
from .ui import InstallUI
from .steps import InstallationSteps
from .execution import StepExecutor
from .utils import check_setup_complete, setup_logging, load_progress, filter_stacks
from utils.precheck import run_precheck


class InstallCLI(BaseCLI):
    """Automated installation of the entire Document Review system."""
    
    def __init__(self):
        super().__init__(
            name="install",
            help_text="Automated installation of the entire Document Review system"
        )
        self.log_dir = Path.home() / ".docr" / "install"
        self.log_file = None
        self.ui = InstallUI()
        self.steps_manager = InstallationSteps()
        self.start_time = None
        self.completed_steps = []
        self.failed_steps = []
        self.last_step_num = 0
        
    def install(self, resume_from: Optional[int] = None, 
                skip_frontend: bool = False,
                timeout: int = 60,
                list_steps: bool = False):
        """Execute full system installation with enhanced UI."""
        
        # Check if setup has been run
        if not check_setup_complete():
            self.ui.show_setup_error()
            return
        
        # If just listing steps, show them and exit
        if list_steps:
            self.steps_manager.list_installation_steps(skip_frontend)
            return
        
        # Run prechecks before installation
        if not run_precheck("install"):
            self.console_utils.print_error("Installation aborted due to missing prerequisites.")
            return
        
        self.start_time = datetime.now()
        
        # Show welcome banner
        self.ui.show_banner()
        
        # Show override warning if applicable
        self.ui.show_override_warning()
        
        # Run docr clean to ensure a clean environment (unless resuming)
        if not resume_from:
            self.console.print("\n[bold cyan]Cleaning Environment[/bold cyan]")
            self.console.print("Running docr clean to ensure a clean installation environment...\n")
            
            import subprocess
            clean_result = subprocess.run(["docr", "clean"], capture_output=False)
            
            if clean_result.returncode != 0:
                self.console_utils.print_warning("Clean command did not complete successfully.")
                if not typer.confirm("Do you want to continue with the installation anyway?"):
                    self.console_utils.print_error("Installation aborted.")
                    return
            else:
                self.console.print("\n[green]✓ Environment cleaned successfully[/green]\n")
        
        # Setup logging
        self.log_file = setup_logging(self.log_dir)
        
        # Get installation steps
        all_steps = self.steps_manager.get_installation_steps(skip_frontend)
        total_original_steps = len(all_steps)
        start_step = resume_from or 1
        
        # If resuming, adjust steps
        if resume_from:
            steps = all_steps[start_step-1:]
            self.console.print(f"\n[yellow]Resuming from step {start_step}[/yellow]\n")
        else:
            steps = all_steps
        
        # Show installation plan
        if not self.ui.show_installation_plan(steps, skip_frontend, resume_from):
            return
        
        # Save progress file path
        progress_file = self.log_dir / "install_progress.json"
        
        # Show log location
        self.ui.show_log_location(self.log_file, self.log_dir)
        
        # Execute installation
        executor = StepExecutor(self.log_file)
        success = executor.execute_installation(
            steps, start_step, progress_file, total_original_steps,
            self.ui, self.completed_steps, self.failed_steps, [self.last_step_num]
        )
        
        # Show summary
        self._show_summary()
        
        if success:
            # Final verification - check deployed stacks
            initials = AppConfig.get_developer_initials()
            self.console.print("\n[bold cyan]🎉 Installation completed successfully![/bold cyan]\n")
            filter_stacks(initials, self._log)
            self.console.print(f"\n📝 Installation log saved to: {self.log_file}")
        else:
            self.console.print("\n[bold red]❌ Installation failed[/bold red]")
            self.console.print(f"\n📝 Check log for details: {self.log_file}")
            
            # Show resume instructions
            if self.last_step_num > 0:
                self.console.print(f"\n💡 To resume from where it failed, run:")
                self.console.print(f"[cyan]docr install --resume-from {self.last_step_num + 1}[/cyan]")
    
    def _log(self, message: str):
        """Write to log file."""
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - {message}\n")
    
    def _show_summary(self):
        """Show installation summary."""
        elapsed = datetime.now() - self.start_time
        
        summary_table = Table(title="Installation Summary", box=box.SIMPLE)
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Value", style="green")
        
        summary_table.add_row("Total Steps", str(len(self.completed_steps) + len(self.failed_steps)))
        summary_table.add_row("Completed", str(len(self.completed_steps)))
        summary_table.add_row("Failed", str(len(self.failed_steps)))
        summary_table.add_row("Duration", str(elapsed).split('.')[0])
        
        self.console.print("\n")
        self.console.print(summary_table)
        
        if self.failed_steps:
            self.console.print("\n[bold red]Failed Steps:[/bold red]")
            for step in self.failed_steps:
                self.console.print(f"  • {step}")


# Export InstallCLI for backward compatibility
__all__ = ['InstallCLI']