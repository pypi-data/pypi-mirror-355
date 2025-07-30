#!/usr/bin/env python3
"""
Credential Store Management CLI.
Manages OpenAI and other API keys in the UMD credential store.
"""
import os
from pathlib import Path
from typing import Optional
import typer
from rich.table import Table

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, ConsoleUtils, CommandUtils
from utils.umd_credential_store import add_credential, get_credential, delete_credential


class CredStoreCLI(BaseCLI):
    """Credential store management CLI."""
    
    def __init__(self):
        # Initialize typer app directly to avoid base CLI auto-commands
        self.app = typer.Typer(
            name="credstore",
            help="Credential store management for API keys",
            rich_markup_mode="rich"
        )
        
        # Initialize console utils
        from utils import ConsoleUtils
        self.console_utils = ConsoleUtils()
        self.console = self.console_utils.console
        
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.command()
        def add(
            key_type: str = typer.Argument(..., help="Type of key to add: 'openai', 'oidc-client-secret' (shared per app), or custom key name"),
            api_key: Optional[str] = typer.Option(None, "--api-key", help="API key value (will prompt if not provided)"),
            force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing key if present"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
        ):
            """Add API key to the credential store. Note: oidc-client-secret is used by oidc-oidcauthorizer-serverless for OIDC authentication flows."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            self.add_credential(key_type, api_key, force)
        
        @self.app.command()
        def verify(
            key_type: str = typer.Argument(..., help="Type of key to verify: 'openai', 'oidc-client-secret', or custom key name"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
        ):
            """Verify API key exists in credential store."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            self.verify_credential(key_type)
        
        @self.app.command()
        def delete(
            key_type: str = typer.Argument(..., help="Type of key to delete: 'openai', 'oidc-client-secret', or custom key name"),
            confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
        ):
            """Delete API key from credential store."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            self.delete_credential(key_type, confirm)
        
        @self.app.command("list")
        def list_cmd(
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
        ):
            """List known credential types and their status."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            self.list_credentials()
        
        @self.app.command()
        def add_from_ssm(
            key_type: str = typer.Argument("openai", help="Type of key to add (default: openai)"),
            ssm_parameter: str = typer.Option("/docr/openai-key", "--ssm-parameter", help="SSM parameter name"),
            force: bool = typer.Option(True, "--force", "-f", help="Overwrite existing key if present"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)"),
        ):
            """Add API key from SSM Parameter Store to credential store."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            self.add_credential_from_ssm(key_type, ssm_parameter, force)
    
    def check_aws_session(self) -> bool:
        """Verify AWS session is valid by listing stacks."""
        cmd = ['aws', 'cloudformation', 'list-stacks', '--page-size', '1']
        success, output = CommandUtils.run_command(cmd, capture_output=True, check=False)
        
        if not success:
            if 'ExpiredToken' in output:
                self.console_utils.print_error("AWS Session token has expired. Please run: umdawslogin login")
            else:
                self.console_utils.print_error(f"AWS credentials error: {output}")
            return False
        return True
    
    def setup_environment(self, key_type: str = None) -> None:
        """Setup environment variables for credential store based on key type."""
        # Get required values from TOML config
        from utils import AppConfig
        credstore_config = AppConfig.get_credstore_config()
        
        dev_initials = credstore_config['dev_initials']
        table_name = credstore_config['table_name']
        environment = f'sandbox-{dev_initials}'
        
        # Use different values based on key type
        if key_type == 'oidc-client-secret':
            # For OIDC client secrets, use the same values as oidc-oidcauthorizer-serverless
            productsuite = 'oidc'
            product = 'oidclambda'
        else:
            # For other keys (like openai), use aisolutions values
            productsuite = 'aisolutions'
            product = credstore_config['product']
        
        # Set environment variables required by credential store
        os.environ.update({
            'UMD_AH_CREDSTORE_TABLENAME': table_name,
            'UMD_AH_ENVIRONMENT': environment,
            'UMD_AH_PRODUCTSUITE': productsuite,
            'UMD_AH_PRODUCT': product
        })
        
        return table_name, environment, productsuite, product
    
    def add_credential(self, key_type: str, api_key: Optional[str], force: bool):
        """Add API key to credential store."""
        # First verify AWS session
        if not self.check_aws_session():
            raise typer.Exit(1)
        
        # Prompt for API key if not provided
        if not api_key:
            api_key = typer.prompt("Enter API key", hide_input=True)
        
        try:
            # Setup environment
            table_name, environment, productsuite, product = self.setup_environment(key_type)
            
            # Store the credential
            add_credential(key_type, api_key, force=force)
            
            self.console_utils.print_success(f"Successfully stored API key as '{key_type}'!")
            
            # Display configuration used
            self.console.print("\n[bold]Configuration used:[/bold]")
            self.console.print(f"  Key name: {key_type}")
            self.console.print(f"  Table: {table_name}")
            self.console.print(f"  Environment: {environment}")
            self.console.print(f"  Product Suite: {productsuite}")
            self.console.print(f"  Product: {product}")
            
        except Exception as e:
            self.console_utils.print_error(f"Failed to store API key: {e}", exit_code=1)
    
    def verify_credential(self, key_type: str):
        """Verify API key exists in credential store."""
        # First verify AWS session
        if not self.check_aws_session():
            raise typer.Exit(1)
        
        try:
            # Setup environment
            self.setup_environment(key_type)
            
            # Check if credential exists
            value = get_credential(key_type)
            
            if value:
                # Mask the key for security
                masked = f"{value[:8]}...{value[-8:]}" if len(value) > 16 else "***"
                self.console_utils.print_success(f"API key '{key_type}' exists: {masked}")
            else:
                self.console_utils.print_warning(f"API key '{key_type}' not found in credential store")
                self.console.print("\nTo add it, run:")
                self.console.print(f"  [cyan]docr credstore add {key_type}[/cyan]")
                
        except Exception as e:
            self.console_utils.print_error(f"Failed to verify API key: {e}", exit_code=1)
    
    def delete_credential(self, key_type: str, confirm: bool):
        """Delete API key from credential store."""
        # First verify AWS session
        if not self.check_aws_session():
            raise typer.Exit(1)
        
        # Confirm deletion unless --yes flag is used
        if not confirm:
            confirm = typer.confirm(f"Are you sure you want to delete credential '{key_type}'?")
            if not confirm:
                self.console.print("Deletion cancelled.")
                return
        
        try:
            # Setup environment
            self.setup_environment(key_type)
            
            # Delete the credential
            delete_credential(key_type)
            
            self.console_utils.print_success(f"Successfully deleted API key '{key_type}'!")
            
        except Exception as e:
            self.console_utils.print_error(f"Failed to delete API key: {e}", exit_code=1)
    
    def add_credential_from_ssm(self, key_type: str, ssm_parameter: str, force: bool):
        """Add API key from SSM Parameter Store to credential store."""
        # First verify AWS session
        if not self.check_aws_session():
            raise typer.Exit(1)
        
        try:
            # Get the API key from SSM
            import boto3
            ssm = boto3.client('ssm', region_name='us-east-1')
            
            self.console_utils.print_info(f"Retrieving key from SSM parameter: {ssm_parameter}")
            
            try:
                response = ssm.get_parameter(Name=ssm_parameter, WithDecryption=True)
                api_key = response['Parameter']['Value']
            except Exception as e:
                self.console_utils.print_error(f"Failed to retrieve SSM parameter: {e}", exit_code=1)
                raise typer.Exit(1)
            
            # Setup environment
            table_name, environment, productsuite, product = self.setup_environment(key_type)
            
            # Store the credential
            add_credential(key_type, api_key, force=force)
            
            self.console_utils.print_success(f"Successfully stored API key as '{key_type}' from SSM!")
            
            # Display configuration used
            self.console.print("\n[bold]Configuration used:[/bold]")
            self.console.print(f"  Key name: {key_type}")
            self.console.print(f"  Table: {table_name}")
            self.console.print(f"  Environment: {environment}")
            self.console.print(f"  Product Suite: {productsuite}")
            self.console.print(f"  Product: {product}")
            self.console.print(f"  SSM Parameter: {ssm_parameter}")
            
        except Exception as e:
            if "Failed to retrieve SSM" not in str(e):
                self.console_utils.print_error(f"Failed to store API key: {e}", exit_code=1)
    
    def list_credentials(self):
        """List known credential types and their status."""
        # First verify AWS session
        if not self.check_aws_session():
            raise typer.Exit(1)
        
        try:
            # Known credential types (note: oidc-client-secret is shared per app, used by oidc-oidcauthorizer-serverless)
            known_types = ['openai', 'oidc-client-secret']
            
            table = Table(title="Credential Store Status")
            table.add_column("Key Type", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Value Preview", style="dim")
            
            for key_type in known_types:
                try:
                    # Setup environment for this specific key type
                    self.setup_environment(key_type)
                    value = get_credential(key_type)
                    if value:
                        masked = f"{value[:6]}...{value[-4:]}" if len(value) > 10 else "***"
                        table.add_row(key_type, "✓ Present", masked)
                    else:
                        table.add_row(key_type, "✗ Missing", "")
                except Exception:
                    table.add_row(key_type, "✗ Missing", "")
            
            self.console.print(table)
            
            self.console.print("\n[dim]To add a missing credential:[/dim]")
            self.console.print("[cyan]docr credstore add <key_type>[/cyan]")
            
        except Exception as e:
            self.console_utils.print_error(f"Failed to list credentials: {e}", exit_code=1)


def main():
    """Main entry point for the credential store CLI."""
    cli = CredStoreCLI()
    cli.app()


if __name__ == "__main__":
    main()