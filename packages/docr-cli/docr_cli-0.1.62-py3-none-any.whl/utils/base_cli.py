#!/usr/bin/env python3
"""
Base CLI class for all Typer-based scripts.
Provides common initialization, configuration, and error handling.
"""
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import typer
from rich.logging import RichHandler

from .config_utils import ConfigUtils
from .console_utils import ConsoleUtils
from .app_config import AppConfig
from .command_utils import CommandUtils
from .aws_utils import AWSUtils
from .system_utils import SystemUtils


class BaseCLI:
    """Base class for CLI applications."""
    
    def __init__(
        self, 
        name: str,
        help_text: str,
        version: str = "1.0.0",
        require_config: bool = True,
        setup_python_path: bool = True
    ):
        """
        Initialize base CLI.
        
        Args:
            name: CLI application name
            help_text: Help text for the CLI
            version: Version string
            require_config: Whether config file is required
            setup_python_path: Whether to set up Python path
        """
        self.name = name
        self.version = version
        self.app = typer.Typer(help=help_text)
        self.console_utils = ConsoleUtils()
        self.console = self.console_utils.console
        
        # Setup Python path if needed
        if setup_python_path:
            AppConfig.setup_python_path()
        
        # Initialize config as None
        self.config: Optional[ConfigUtils] = None
        self.require_config = require_config
        
        # Set up logging
        self.setup_logging()
        
        # Add common commands
        self._add_common_commands()
    
    def setup_logging(self, level: str = "INFO") -> None:
        """
        Set up logging with Rich handler.
        
        Args:
            level: Default log level
        """
        # Get log level from environment or use default
        import os
        log_level = os.environ.get("LOG_LEVEL", level).upper()
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=self.console, rich_tracebacks=True)]
        )
        
        self.logger = logging.getLogger(self.name)
    
    def load_config(self, stage: str = "sandbox", app_name: Optional[str] = None) -> ConfigUtils:
        """
        Load configuration for the given stage.
        
        Args:
            stage: Environment stage
            app_name: Optional application name (auto-detected if not provided)
            
        Returns:
            ConfigUtils instance
            
        Raises:
            typer.Exit: If config is required but not found
        """
        try:
            self.config = ConfigUtils(stage, app_name)
            self.logger.info(f"Loaded configuration for stage: {stage}")
            return self.config
        except FileNotFoundError as e:
            if self.require_config:
                self.console_utils.print_error(str(e), exit_code=1)
            else:
                self.logger.warning(f"Config not found: {e}")
                return None
        except ValueError as e:
            # Handle app detection error
            if self.require_config:
                self.console_utils.print_error(str(e), exit_code=1)
            else:
                self.logger.warning(f"Config not found: {e}")
                return None
    
    def _add_common_commands(self) -> None:
        """Add common commands to the CLI."""
        # Common commands have been removed to reduce CLI redundancy
        # version and config-path are now only available at the top level
        pass
    
    def handle_error(self, error: Exception, debug: bool = False) -> None:
        """
        Handle errors with consistent formatting.
        
        Args:
            error: Exception to handle
            debug: Whether to show full traceback
        """
        error_details = self.console_utils.format_error_details(error, debug)
        self.console.print(error_details)
        
        if not debug:
            self.console.print("\n[dim]Run with --debug for full traceback[/dim]")
    
    def validate_aws_credentials(self) -> bool:
        """
        Validate AWS credentials are configured.
        
        Returns:
            True if valid
        """
        if not CommandUtils.check_aws_credentials():
            self.console_utils.print_error(
                "AWS credentials not configured or expired.\n"
                "Please run: aws configure"
            )
            return False
        return True
    
    def check_prerequisites(self, require_docker: bool = True, require_aws: bool = True) -> bool:
        """
        Check system prerequisites (Docker, AWS credentials, etc.).
        
        Args:
            require_docker: Whether Docker is required
            require_aws: Whether AWS credentials are required
            
        Returns:
            True if all prerequisites are met
        """
        self.console.print("\n[bold cyan]Checking Prerequisites...[/bold cyan]")
        
        all_checks_passed = True
        
        # Check AWS credentials
        if require_aws:
            aws_valid, aws_msg = AWSUtils.verify_aws_token()
            self.console.print(aws_msg)
            if not aws_valid:
                all_checks_passed = False
        
        # Check Docker
        if require_docker:
            docker_valid, docker_msg = SystemUtils.verify_docker()
            self.console.print(docker_msg)
            if not docker_valid:
                all_checks_passed = False
        
        # Final status
        if all_checks_passed:
            self.console_utils.print_success("Prerequisites check passed")
        else:
            self.console_utils.print_error("Prerequisites check failed")
            return False
        
        return True
    
    def validate_required_commands(self, commands: List[str]) -> bool:
        """
        Validate required commands are available.
        
        Args:
            commands: List of command names to check
            
        Returns:
            True if all commands are available
        """
        missing = []
        for cmd in commands:
            if not CommandUtils.check_command_exists(cmd):
                missing.append(cmd)
        
        if missing:
            self.console_utils.print_error(
                f"Missing required commands: {', '.join(missing)}\n"
                f"Please install these tools and try again."
            )
            return False
        
        return True
    
    def get_stack_name(self) -> Optional[str]:
        """
        Get CloudFormation stack name from TOML config.
        
        Returns:
            Stack name or None
        """
        # Get from TOML config
        stack_name = AppConfig.get_stack_name()
        
        if not stack_name:
            # Try environment as fallback
            import os
            stack_name = os.environ.get('SCRIPT_STACK_NAME')
        
        return stack_name
    
    def run(self) -> None:
        """Run the CLI application."""
        try:
            self.app()
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
            sys.exit(130)
        except typer.Exit:
            raise
        except Exception as e:
            self.handle_error(e, debug=False)
            sys.exit(1)
    
    def create_global_options(self):
        """
        Create common global options decorator.
        
        Returns:
            Decorator function for adding common options
        """
        def decorator(func):
            func = typer.Option(False, "--debug", "-d", help="Enable debug output")(func)
            func = typer.Option("sandbox", "--stage", "-s", help="Environment stage")(func)
            func = typer.Option(False, "--verbose", "-v", help="Enable verbose output")(func)
            return func
        return decorator
    
    def display_results(self, results: List[Tuple[str, bool]], title: str = "Results") -> bool:
        """
        Display results summary table.
        
        Args:
            results: List of (name, success) tuples
            title: Table title
            
        Returns:
            True if all results were successful
        """
        table = self.console_utils.create_summary_table(results, title)
        self.console.print(table)
        
        # Check overall success
        all_success = all(success for _, success in results)
        
        if all_success:
            self.console_utils.print_success("All operations completed successfully!")
        else:
            failed = [name for name, success in results if not success]
            self.console_utils.print_error(
                f"Failed operations: {', '.join(failed)}"
            )
        
        return all_success
    
    def prompt_for_value(
        self, 
        prompt: str, 
        default: Optional[str] = None,
        hide_input: bool = False,
        choices: Optional[List[str]] = None
    ) -> str:
        """
        Prompt user for input with validation.
        
        Args:
            prompt: Prompt message
            default: Default value
            hide_input: Whether to hide input (for passwords)
            choices: List of valid choices
            
        Returns:
            User input
        """
        if choices:
            return typer.prompt(
                prompt,
                default=default,
                type=typer.Choice(choices)
            )
        else:
            return typer.prompt(
                prompt,
                default=default,
                hide_input=hide_input
            )