"""
Precheck module for validating system requirements.
Checks for required commands and their versions before running install or setup.
"""
import subprocess
import re
from typing import Dict, Tuple, Optional, List
from packaging import version
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from .console_utils import ConsoleUtils
from .system_utils import SystemUtils


class PrecheckResult:
    """Container for precheck results."""
    def __init__(self):
        self.all_passed = True
        self.results = {}
        self.warnings = []
        self.errors = []


class Precheck:
    """System requirements validation."""
    
    # Required commands with minimum versions (major.minor)
    REQUIRED_COMMANDS = {
        'aws': {
            'min_version': '2.13',
            'version_pattern': r'aws-cli/(\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'AWS CLI'
        },
        'sam': {
            'min_version': '1.100',
            'version_pattern': r'version (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'SAM CLI'
        },
        'docker': {
            'min_version': '20.10',
            'version_pattern': r'Docker version (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'Docker',
            'check_running': True
        },
        'npm': {
            'min_version': '10.8',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'npm'
        },
        'node': {
            'min_version': '20.0',
            'version_pattern': r'v(\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'Node.js'
        },
        'poetry': {
            'min_version': '1.8',
            'version_pattern': r'Poetry.*version (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'Poetry'
        },
        'python': {
            'min_version': '3.11',
            'version_pattern': r'Python (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'Python'
        },
        'git': {
            'min_version': '2.0',
            'version_pattern': r'git version (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'Git'
        },
        'umdawslogin': {
            'min_version': '0.1.61',
            'version_pattern': r'umdawslogin version: (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'UMD AWS Login'
        },
        'pipx': {
            'min_version': '1.7.1',
            'version_pattern': r'(\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'pipx'
        },
        'brew': {
            'min_version': '4.0',
            'version_pattern': r'Homebrew (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'Homebrew (macOS)'
        }
    }
    
    # Optional commands (warn if missing but don't fail)
    OPTIONAL_COMMANDS = {
        'zellij': {
            'min_version': '0.34',
            'version_pattern': r'zellij (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'zellij'
        },
        'isort': {
            'min_version': '5.0',
            'version_pattern': r'VERSION (\d+\.\d+\.\d+)',
            'version_flag': '--version',
            'name': 'isort'
        }
    }
    
    def __init__(self):
        self.console = Console()
        self.console_utils = ConsoleUtils()
        self.system_utils = SystemUtils()
    
    def check_command_version(self, command: str, config: Dict) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if a command exists and meets version requirements.
        
        Returns:
            Tuple of (success, actual_version, error_message)
        """
        try:
            # Check if command exists
            result = subprocess.run(
                [command, config['version_flag']],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                return False, None, f"{config['name']} not found or not accessible"
            
            # Extract version
            version_match = re.search(config['version_pattern'], result.stdout + result.stderr)
            if not version_match:
                return True, "unknown", f"Could not parse {config['name']} version"
            
            actual_version = version_match.group(1)
            
            # Compare versions (major.minor only)
            if 'min_version' in config:
                actual_parts = actual_version.split('.')[:2]
                required_parts = config['min_version'].split('.')[:2]
                
                actual_mm = '.'.join(actual_parts)
                required_mm = '.'.join(required_parts)
                
                if version.parse(actual_mm) < version.parse(required_mm):
                    return False, actual_version, f"{config['name']} version {actual_version} is below minimum {config['min_version']}"
            
            return True, actual_version, None
            
        except subprocess.TimeoutExpired:
            return False, None, f"{config['name']} command timed out"
        except FileNotFoundError:
            return False, None, f"{config['name']} not installed"
        except Exception as e:
            return False, None, f"Error checking {config['name']}: {str(e)}"
    
    def check_docker_running(self) -> Tuple[bool, str]:
        """Check if Docker daemon is running."""
        try:
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "Docker daemon is running"
            else:
                return False, "Docker daemon is not running. Please start Docker Desktop."
                
        except subprocess.TimeoutExpired:
            return False, "Docker daemon not responding. Please restart Docker Desktop."
        except Exception as e:
            return False, f"Error checking Docker status: {str(e)}"
    
    def run_prechecks(self, context: str = "install") -> bool:
        """
        Run all prechecks and return whether to proceed.
        
        Args:
            context: Context for the check (e.g., "install", "setup")
            
        Returns:
            True if user wants to proceed, False otherwise
        """
        self.console.print(f"\n[bold cyan]System Requirements Check for {context.title()}[/bold cyan]\n")
        
        result = PrecheckResult()
        
        # Create results table
        table = Table(title="Command Availability", show_header=True)
        table.add_column("Command", style="cyan")
        table.add_column("Type", style="dim")
        table.add_column("Status", style="bold")
        table.add_column("Version", style="dim")
        table.add_column("Min Required", style="dim")
        
        # Check required commands
        for command, config in self.REQUIRED_COMMANDS.items():
            success, actual_version, error_msg = self.check_command_version(command, config)
            
            if success:
                status = "[green]✓ Available[/green]"
                version_str = actual_version or "unknown"
            else:
                status = "[red]✗ Failed[/red]"
                version_str = actual_version or "not found"
                result.all_passed = False
                result.errors.append(error_msg)
            
            min_ver = config.get('min_version', 'any')
            table.add_row(config['name'], "Required", status, version_str, f">= {min_ver}")
            
            # Special check for Docker daemon
            if command == 'docker' and success and config.get('check_running'):
                docker_running, docker_msg = self.check_docker_running()
                if not docker_running:
                    table.add_row("Docker Daemon", "Required", "[red]✗ Not Running[/red]", "-", "-")
                    result.errors.append(docker_msg)
                    result.all_passed = False
                else:
                    table.add_row("Docker Daemon", "Required", "[green]✓ Running[/green]", "-", "-")
        
        # Check optional commands
        for command, config in self.OPTIONAL_COMMANDS.items():
            success, actual_version, error_msg = self.check_command_version(command, config)
            
            if success:
                status = "[green]✓ Available[/green]"
                version_str = actual_version or "unknown"
            else:
                status = "[yellow]○ Not Found[/yellow]"
                version_str = "-"
                result.warnings.append(f"{config['name']} is not installed")
            
            min_ver = config.get('min_version', 'any')
            table.add_row(config['name'], "[dim]Optional[/dim]", status, version_str, f">= {min_ver}")
        
        # Display results
        self.console.print(table)
        self.console.print()
        
        # Show errors with install instructions
        if result.errors:
            self.console_utils.print_error("The following issues were found:")
            install_instructions = self.get_install_instructions()
            
            for error in result.errors:
                self.console.print(f"  • {error}", style="red")
                # Extract command name from error message
                for cmd, config in {**self.REQUIRED_COMMANDS, **self.OPTIONAL_COMMANDS}.items():
                    if config['name'] in error and cmd in install_instructions:
                        self.console.print(f"    → {install_instructions[cmd]}", style="dim")
                        break
            self.console.print()
        
        # Show warnings with install instructions
        if result.warnings:
            self.console_utils.print_warning("Optional components:")
            install_instructions = self.get_install_instructions()
            
            for warning in result.warnings:
                self.console.print(f"  • {warning}", style="yellow")
                # Extract command name from warning message
                for cmd, config in self.OPTIONAL_COMMANDS.items():
                    if config['name'] in warning and cmd in install_instructions:
                        self.console.print(f"    → {install_instructions[cmd]}", style="dim")
                        break
            self.console.print()
        
        # Determine action
        if result.all_passed:
            self.console_utils.print_success("All required system checks passed!")
            return True
        else:
            self.console_utils.print_warning(
                f"Some required commands are missing or outdated. "
                f"The {context} process may fail without these dependencies."
            )
            
            # Ask user if they want to proceed
            return Confirm.ask(
                "\n[yellow]Do you want to proceed anyway?[/yellow]",
                default=False
            )
    
    @staticmethod
    def get_install_instructions() -> Dict[str, str]:
        """Get platform-specific installation instructions."""
        return {
            'aws': 'brew install awscli OR download from https://aws.amazon.com/cli/',
            'sam': 'pipx install aws-sam-cli',
            'docker': 'Download Docker Desktop from https://www.docker.com/products/docker-desktop',
            'npm': 'Install Node.js (includes npm) from https://nodejs.org/',
            'node': 'brew install node OR download from https://nodejs.org/',
            'poetry': 'pipx install poetry OR curl -sSL https://install.python-poetry.org | python3 -',
            'python': 'brew install python@3.12 OR download from https://www.python.org/',
            'git': 'brew install git OR download from https://git-scm.com/',
            'umdawslogin': 'pipx install umdawslogin',
            'pipx': 'brew install pipx OR python3 -m pip install --user pipx',
            'brew': 'Visit https://brew.sh/ for installation instructions',
            'zellij': 'brew install zellij',
            'isort': 'pipx install isort'
        }


def run_precheck(context: str = "operation") -> bool:
    """
    Convenience function to run prechecks.
    
    Args:
        context: Context for the check (e.g., "install", "setup")
        
    Returns:
        True if checks pass or user chooses to proceed, False otherwise
    """
    precheck = Precheck()
    return precheck.run_prechecks(context)