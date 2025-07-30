"""Base class for all doctor verification checks."""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from utils import ConsoleUtils, AppConfig


class BaseDoctorCheck(ABC):
    """Base class for all doctor verification checks."""
    
    def __init__(self, stage: str = "sandbox", verbose: bool = False, fix: bool = False):
        self.stage = stage
        self.verbose = verbose
        self.fix = fix
        self.console_utils = ConsoleUtils()
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'fixed': 0,
            'details': []
        }
    
    @abstractmethod
    def check(self) -> bool:
        """Run the verification check. Returns True if all checks pass."""
        pass
    
    def log_result(self, check_name: str, passed: bool, message: str, fix_attempted: bool = False):
        """Log a check result with consistent formatting."""
        status = "✅" if passed else "❌"
        fix_indicator = " 🔧" if fix_attempted else ""
        
        # Enhanced formatting with proper indentation and spacing
        self.console_utils.console.print(
            f"    {status}{fix_indicator} [bold]{check_name}[/bold]: [dim]{message}[/dim]"
        )
        
        if passed:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
            
        if fix_attempted:
            self.results['fixed'] += 1
            
        self.results['details'].append({
            'check': check_name,
            'passed': passed,
            'message': message,
            'fix_attempted': fix_attempted
        })
    
    @staticmethod
    def get_simple_config_path(app_name: str, stage: str = "sandbox") -> Path:
        """Get config file path using simple fixed directory structure for doctor commands."""
        # Use the fixed directory structure from project root
        project_root = AppConfig.get_project_root()
        
        # Map app names to their backend directories
        app_backend_dirs = {
            "legislative-review": "aisolutions-docreview-serverless/legislative-review-backend",
            "oidc-manager": "oidc-oidcmanager-serverless/oidc-manager-backend",
            "costs": "aisolutions-costsmodule-serverless/cost-component-backend",
            "jobs": "aisolutions-jobsmodule-serverless/jobs-component-backend",
            "workspaces": "aisolutions-workspaces-serverless/workspaces-component-backend"
        }
        
        if app_name not in app_backend_dirs:
            raise ValueError(f"Unknown app: {app_name}. Known apps: {list(app_backend_dirs.keys())}")
        
        backend_dir = project_root / app_backend_dirs[app_name]
        config_path = backend_dir / "config" / f"config.{stage}"
        
        return config_path
    
    def print_summary(self, title: str):
        """Print enhanced summary of check results with better styling."""
        total = self.results['passed'] + self.results['failed']
        if total == 0:
            self.console_utils.print_warning(f"{title}: No checks performed")
            return
        
        # Create a more visually appealing summary
        from rich.panel import Panel
        from rich.text import Text
        
        # Summary content
        summary_text = Text()
        
        if self.results['failed'] == 0:
            summary_text.append("🎉 All checks passed! ", style="bold green")
            summary_text.append(f"({self.results['passed']}/{total})", style="dim")
        else:
            summary_text.append("⚠️  Some checks failed ", style="bold yellow")
            summary_text.append(f"({self.results['passed']}/{total} passed)", style="dim")
        
        if self.results['fixed'] > 0:
            summary_text.append("\n🔧 ", style="")
            summary_text.append(f"{self.results['fixed']} issues auto-fixed", style="blue")
        
        # Create a compact summary panel
        panel = Panel(
            summary_text,
            title=f"[bold]{title} Summary[/bold]",
            border_style="blue" if self.results['failed'] == 0 else "yellow",
            padding=(0, 1)
        )
        
        self.console_utils.console.print(panel)
        self.console_utils.console.print()  # Add spacing