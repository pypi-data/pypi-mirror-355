#!/usr/bin/env python3
"""
Unified Lambda configuration CLI for managing log levels and scheduler.
Cross-platform replacement for set_log_level.sh and toggle_scheduler.sh.
"""
import re
from pathlib import Path
from typing import Optional
from enum import Enum
import typer
from rich.table import Table
from rich.prompt import Confirm

# Add parent directory to Python path for imports
import sys
sys.path.append(str(Path(__file__).parent))

from utils import BaseCLI, ConfigUtils, ConsoleUtils, CommandUtils


class LogLevel(str, Enum):
    """Valid log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class SchedulerState(str, Enum):
    """Scheduler states."""
    ENABLE = "enable"
    DISABLE = "disable"


class LambdaConfigCLI(BaseCLI):
    """Lambda configuration management CLI."""
    
    def __init__(self):
        super().__init__(
            name="lambda-config",
            help_text="Manage Lambda configuration settings",
            require_config=False,  # Config is optional for some commands
            setup_python_path=False  # Don't require config for setup
        )
    
    def get_config_path(self, app: str, environment: Optional[str] = None) -> Path:
        """Get the config file path for the given environment."""
        if not environment:
            # Default to sandbox if not specified
            environment = "sandbox"
        
        from utils import AppConfig
        
        return AppConfig.get_config_dir(app) / f"config.{environment}"
    
    def update_config_file(self, config_path: Path, key: str, value: str) -> bool:
        """Update or add a key-value pair in the config file."""
        if not config_path.exists():
            cli.console_utils.print_error(f"Config file not found: {config_path}", exit_code=1)
            return False
        
        # Read the file
        lines = config_path.read_text().splitlines()
        
        # Check if key exists
        updated = False
        new_lines = []
        
        for line in lines:
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                updated = True
            else:
                new_lines.append(line)
        
        # If key didn't exist, add it
        if not updated:
            new_lines.append(f"{key}={value}")
        
        # Write back
        config_path.write_text('\n'.join(new_lines) + '\n')
        return True
    
    def get_stack_name(self, app: str, config: Optional[ConfigUtils] = None) -> Optional[str]:
        """Get the stack name from TOML config."""
        from utils import AppConfig
        
        # Get stack name from TOML config
        stack_name = AppConfig.get_stack_name(app)
        if stack_name:
            return stack_name
        
        # Fallback to reading from samconfig.toml
        samconfig_path = AppConfig.get_app_backend_dir(app) / "samconfig.toml"
        if samconfig_path.exists():
            content = samconfig_path.read_text()
            match = re.search(r'stack_name\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        
        return None
    
    def get_lambda_function_name(self, config: Optional[ConfigUtils] = None) -> Optional[str]:
        """Get Lambda function name from TOML config."""
        from utils import AppConfig
        
        # Get Lambda function name from TOML config
        function_name = AppConfig.get_lambda_function_name()
        
        if not function_name:
            # If not found, prompt to run refresh
            self.console_utils.print_error(
                "Lambda function name not found in configuration.\n"
                "Run 'docr refresh' to update configuration from AWS."
            )
            raise typer.Exit(1)
        
        return function_name


# Create CLI instance
cli = LambdaConfigCLI()
app = cli.app


@app.command()
def log_level(
    level: LogLevel = typer.Argument(..., help="Log level to set"),
    app: str = typer.Option(..., "--app", "-a", help="Application name (required)"),
    environment: Optional[str] = typer.Option(None, "--env", "-e", help="Environment (default: from config)"),
    update_lambda: bool = typer.Option(False, "--update-lambda", "-u", help="Also update Lambda function configuration"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
):
    """Set the LOG_LEVEL in the config file and optionally update Lambda."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    config_path = cli.get_config_path(app, environment)
    
    ConsoleUtils.header(f"Setting LOG_LEVEL to {level} in {config_path}")
    
    if cli.update_config_file(config_path, "LOG_LEVEL", level):
        ConsoleUtils.success(f"Successfully updated LOG_LEVEL to {level}")
        
        # Check if we should update Lambda
        if update_lambda:
            try:
                config = ConfigUtils()
                function_name = cli.get_lambda_function_name(config)
            except Exception:
                function_name = None
            
            if function_name:
                cli.console.print(f"[blue]Updating Lambda function: {function_name}[/blue]")
                
                cmd = [
                    "aws", "lambda", "update-function-configuration",
                    "--function-name", function_name,
                    "--environment", f"Variables={{LOG_LEVEL={level}}}"
                ]
                
                success, output = CommandUtils.run_command(cmd, capture_output=True)
                
                if success:
                    ConsoleUtils.success("Lambda function configuration updated")
                    ConsoleUtils.warning("It may take a few seconds for changes to take effect")
                else:
                    self.console_utils.print_error(f"Failed to update Lambda: {output}", exit_code=1)
            else:
                ConsoleUtils.warning(
                    "No Lambda function name found.\n"
                    "Run 'docr refresh' to update configuration and enable Lambda updates."
                )
        else:
            cli.console.print("[blue]Local environment updated. Restart your application for changes to take effect.[/blue]")
    else:
        self.console_utils.print_error("Failed to update LOG_LEVEL", exit_code=1)
        raise typer.Exit(1)


@app.command()
def scheduler(
    action: SchedulerState = typer.Argument(..., help="Enable or disable the scheduler"),
    app: str = typer.Option(..., "--app", "-a", help="Application name (required)"),
    stack_update: bool = typer.Option(True, "--stack-update/--full-deploy", help="Update stack directly vs full redeployment"),
    stack_name: Optional[str] = typer.Option(None, "--stack", "-s", help="CloudFormation stack name"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
):
    """Enable or disable the scheduler for the legislative-review stack."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    enable_value = "true" if action == SchedulerState.ENABLE else "false"
    action_verb = "Enabling" if action == SchedulerState.ENABLE else "Disabling"
    
    ConsoleUtils.header(f"{action_verb} scheduler...")
    
    # Get stack name
    if not stack_name:
        try:
            config = ConfigUtils()
            stack_name = cli.get_stack_name(app, config)
        except Exception:
            stack_name = None
        if not stack_name:
            self.console_utils.print_error(
                "Could not determine stack name.\n"
                "Please provide with --stack option or run 'docr refresh' to update configuration.",
                exit_code=1
            )
    
    if stack_update:
        # Update CloudFormation stack directly
        if not Confirm.ask(f"Update existing stack '{stack_name}' without redeployment?", default=True):
            stack_update = False
    
    if stack_update:
        cli.console.print(f"[blue]Updating CloudFormation stack: {stack_name}[/blue]")
        
        cmd = [
            "aws", "cloudformation", "update-stack",
            "--stack-name", stack_name,
            "--use-previous-template",
            "--parameters",
            "ParameterKey=AppKey,UsePreviousValue=true",
            "ParameterKey=DeveloperInitialsLowercase,UsePreviousValue=true",
            f"ParameterKey=EnableScheduler,ParameterValue={enable_value}",
            "--capabilities", "CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND"
        ]
        
        success, output = CommandUtils.run_command(cmd, capture_output=True)
        
        if success:
            ConsoleUtils.success("Stack update initiated")
            cli.console.print("[blue]Check the AWS console for status[/blue]")
        else:
            if "No updates are to be performed" in output:
                ConsoleUtils.warning("No changes needed - scheduler already in desired state")
            else:
                self.console_utils.print_error(f"Stack update failed: {output}", exit_code=1)
                raise typer.Exit(1)
    else:
        # Update samconfig.toml and redeploy
        cli.console.print("[blue]Updating samconfig.toml and redeploying...[/blue]")
        
        from utils import AppConfig
        samconfig_path = AppConfig.get_app_backend_dir(app) / "samconfig.toml"
        if not samconfig_path.exists():
            self.console_utils.print_error(f"samconfig.toml not found at: {samconfig_path}", exit_code=1)
            raise typer.Exit(1)
        
        # Read and update samconfig.toml
        content = samconfig_path.read_text()
        updated_content = re.sub(
            r'EnableScheduler=\\"[^\\"]*\\"',
            f'EnableScheduler=\\"{enable_value}\\"',
            content
        )
        
        if content != updated_content:
            samconfig_path.write_text(updated_content)
            ConsoleUtils.success("samconfig.toml updated successfully")
            
            # Run SAM deploy
            cli.console.print("[blue]Starting deployment...[/blue]")
            
            success, _ = CommandUtils.run_command(["sam", "deploy"])
            if success:
                ConsoleUtils.success("Deployment completed successfully")
            else:
                self.console_utils.print_error("Deployment failed. See error message above.", exit_code=1)
                raise typer.Exit(1)
        else:
            ConsoleUtils.warning("No changes needed in samconfig.toml")


@app.command()
def show(
    app: str = typer.Option(..., "--app", "-a", help="Application name (required)"),
    environment: Optional[str] = typer.Option(None, "--env", "-e", help="Environment (default: from config)"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
):
    """Show current configuration settings."""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    config_path = cli.get_config_path(app, environment)
    
    if not config_path.exists():
        cli.console_utils.print_error(f"Config file not found: {config_path}", exit_code=1)
    
    # Read current settings
    config_content = config_path.read_text()
    
    # Extract values
    log_level = "Not set"
    for line in config_content.splitlines():
        if line.startswith("LOG_LEVEL="):
            log_level = line.split("=", 1)[1]
            break
    
    # Get stack info
    try:
        config = ConfigUtils()
        stack_name = cli.get_stack_name(config) or "Not determined"
        env = config.stage
    except Exception:
        stack_name = "Not determined"
        env = environment or "sandbox"
    
    # Check scheduler state from samconfig
    scheduler_state = "Unknown"
    from utils import AppConfig
    samconfig_path = AppConfig.get_app_backend_dir(app) / "samconfig.toml"
    if samconfig_path.exists():
        content = samconfig_path.read_text()
        match = re.search(r'EnableScheduler=\\"([^\\"]*)\\"', content)
        if match:
            scheduler_state = "Enabled" if match.group(1).lower() == "true" else "Disabled"
    
    # Display table
    table = ConsoleUtils.create_table(f"Configuration Settings ({env})")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")
    
    table.add_row("Config File", str(config_path))
    table.add_row("LOG_LEVEL", log_level)
    table.add_row("Stack Name", stack_name)
    table.add_row("Scheduler", scheduler_state)
    
    cli.console.print(table)


@app.command()
def list_levels():
    """List all available log levels."""
    table = ConsoleUtils.create_table("Available Log Levels")
    table.add_column("Level", style="cyan")
    table.add_column("Description")
    
    table.add_row("DEBUG", "Detailed information, typically of interest only when diagnosing problems")
    table.add_row("INFO", "Confirmation that things are working as expected")
    table.add_row("WARNING", "An indication that something unexpected happened")
    table.add_row("ERROR", "Due to a more serious problem, the software has not been able to perform some function")
    table.add_row("CRITICAL", "A serious error, indicating that the program itself may be unable to continue running")
    
    cli.console.print(table)


if __name__ == "__main__":
    app()