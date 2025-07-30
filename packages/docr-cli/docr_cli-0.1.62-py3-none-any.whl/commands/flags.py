#!/usr/bin/env python3
"""
Global feature flags management CLI.
Manages feature flags across all components using a unified approach.
"""
import yaml
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
import typer
from rich.table import Table

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, ConfigUtils, JWTUtils, ConsoleUtils, DirectInvokeClient
from commands.refresh import refresh_config
from loguru import logger


class FeatureFlagsCLI(BaseCLI):
    """Global feature flags management CLI."""
    
    def __init__(self):
        super().__init__(
            name="feature-flags",
            help_text="Global feature flags management across all components.\n\n"
                     "Synchronizes flags from config/flags/flags.yml to all components.",
            require_config=False,  # We might run without full config
            setup_python_path=False  # Don't require config for setup
        )
        
        # Default flags file location will be set dynamically
        self.flags_file = None
        
        # Initialize with dynamic application detection
        from utils import AppConfig
        
        # Valid components (applications + components)
        self.valid_components = AppConfig.discover_applications() + AppConfig.discover_components()
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.command()
        def sync(
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage"),
            components: str = typer.Option(..., "--components", "-c", help="Comma-separated list of components to sync (required)"),
            auth_type: Optional[str] = typer.Option(None, "--auth-type", "-u", help="Override auth type: 'direct' or 'oidc'"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
        ):
            """Sync all flags from flags.yml to components."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            
            if not verbose:
                logger.remove()  # Remove default handler
                logger.add(lambda msg: None)  # Add null handler to suppress all logs
            
            component_list = [c.strip() for c in components.split(',')]
            self.sync_flags(stage, component_list, auth_type)
        
        @self.app.command()
        def set(
            flag_name: str = typer.Argument(..., help="Name of the flag to set"),
            value: bool = typer.Argument(..., help="Flag value (true/false)"),
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage"),
            reason: str = typer.Option("manual_override", "--reason", "-r", help="Reason for the change"),
            components: str = typer.Option(..., "--components", "-c", help="Comma-separated list of components (required)"),
            auth_type: Optional[str] = typer.Option(None, "--auth-type", "-u", help="Override auth type: 'direct' or 'oidc'"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
        ):
            """Set a specific feature flag value across components."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            
            if not verbose:
                logger.remove()  # Remove default handler
                logger.add(lambda msg: None)  # Add null handler to suppress all logs
            
            component_list = [c.strip() for c in components.split(',')]
            self.set_flag(stage, flag_name, value, reason, component_list, auth_type)
        
        @self.app.command()
        def get(
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage"),
            flag_name: Optional[str] = typer.Option(None, "--flag", "-f", help="Specific flag to get"),
            components: str = typer.Option(..., "--components", "-c", help="Comma-separated list of components (required)"),
            auth_type: Optional[str] = typer.Option(None, "--auth-type", "-u", help="Override auth type: 'direct' or 'oidc'"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
        ):
            """Get feature flag values from components."""
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            
            if not verbose:
                logger.remove()  # Remove default handler
                logger.add(lambda msg: None)  # Add null handler to suppress all logs
            
            component_list = [c.strip() for c in components.split(',')]
            self.get_flags(stage, flag_name, component_list, auth_type)
        
        @self.app.command()
        def list(
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
        ):
            """List all available feature flags from flags.yml."""
            if not verbose:
                logger.remove()  # Remove default handler
                logger.add(lambda msg: None)  # Add null handler to suppress all logs
            
            self.list_flags()
    
    def load_flags_config(self) -> Dict[str, Any]:
        """Load flags configuration from YAML file."""
        # Find flags file dynamically
        if self.flags_file is None:
            # Try to find flags.yml in current directory or parent directories
            cwd = Path.cwd()
            possible_paths = [
                cwd / "config" / "flags" / "flags.yml",
                cwd / "flags" / "flags.yml",
                cwd / "flags.yml"
            ]
            
            # Also check parent directories
            for parent in cwd.parents:
                if (parent / "config" / "flags" / "flags.yml").exists():
                    possible_paths.append(parent / "config" / "flags" / "flags.yml")
                    break
            
            for path in possible_paths:
                if path.exists():
                    self.flags_file = path
                    self.console_utils.print_info(f"Found flags file: {path}")
                    break
            
            if self.flags_file is None:
                self.console_utils.print_error(
                    "Could not find flags.yml file.\n"
                    "Expected locations:\n" +
                    "\n".join(f"  - {p}" for p in possible_paths[:3]),
                    exit_code=1
                )
        
        if not self.flags_file.exists():
            self.console_utils.print_error(
                f"Flags file not found: {self.flags_file}",
                exit_code=1
            )
        
        with open(self.flags_file) as f:
            return yaml.safe_load(f)
    
    def validate_components(self, components: List[str]) -> None:
        """Validate that all components are valid."""
        invalid_components = [c for c in components if c not in self.valid_components]
        if invalid_components:
            self.console_utils.print_error(
                f"Invalid component(s): {', '.join(invalid_components)}\n"
                f"Valid components: {', '.join(self.valid_components)}",
                exit_code=1
            )
    
    def get_api_url(self, component: str, stage: str) -> str:
        """Get the API URL for a specific component."""
        from utils.api_utils import get_api_url_for_service
        return get_api_url_for_service(component, self.console_utils, stage=stage)
    
    def get_auth_method(self, component: str, stage: str, auth_type: Optional[str] = None) -> tuple[str, Any]:
        """Get authentication method (reusing bootstrap auth logic)."""
        # Determine auth type based on stage if not explicitly provided
        if auth_type is None:
            auth_type = "direct" if stage == "sandbox" else "oidc"
        
        # Validate auth type
        if auth_type not in ["direct", "oidc"]:
            self.console_utils.print_error(f"Invalid auth type '{auth_type}'. Must be 'direct' or 'oidc'.", exit_code=1)
        
        # Get appropriate method
        if auth_type == "direct":
            return "direct", DirectInvokeClient(component, stage)
        else:
            return "oidc", self.get_oidc_token(stage)
    
    
    def get_oidc_token(self, stage: str = "sandbox") -> str:
        """Get OIDC user token from saved file."""
        ssh_dir = Path.home() / ".ssh"
        ssh_dir.mkdir(exist_ok=True)
        token_file = ssh_dir / f"docr.oidc.token.{stage}.txt"
        
        # Check if we have a saved token
        if token_file.exists():
            with open(token_file) as f:
                saved_token = f.read().strip()
            
            # Validate token format
            if JWTUtils.validate_token_format(saved_token):
                # Check expiry
                is_valid, time_remaining = JWTUtils.check_expiry(saved_token)
                
                if is_valid:
                    time_str = JWTUtils.format_time_remaining(time_remaining)
                    self.console_utils.print_info(f"Using saved token (expires in {time_str})")
                    return saved_token
                else:
                    self.console_utils.print_error("Saved token has expired")
            else:
                self.console_utils.print_error("Saved token format is invalid")
        
        # No valid saved token found
        self.console_utils.print_error("No valid authentication token found!")
        self.console.print("\n[bold]To set up your token:[/bold]")
        self.console.print("1. Login to the legislative app in your browser")
        self.console.print("2. Open Developer Tools (F12)")
        self.console.print("3. Look in the Console for your authorization token")
        self.console.print("4. It will look like: [yellow]Bearer OIDC_USER_JWT:eyJraWQ...[/yellow]")
        self.console.print("5. Copy the ENTIRE token including 'Bearer OIDC_USER_JWT:'")
        self.console.print("\n[bold]Then save it to the token file:[/bold]")
        self.console.print(f"[cyan]echo 'YOUR_FULL_TOKEN_HERE' > {token_file}[/cyan]")
        
        raise typer.Exit(1)
    
    def sync_flags(self, stage: str, components: List[str], auth_type: Optional[str]):
        """Sync all flags from flags.yml to components."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        self.console.print(f"[bold]Syncing feature flags for stage: {stage}[/bold]\n")
        
        # Load flags configuration
        flags_config = self.load_flags_config()
        
        # Components are now required from the command
        
        # Validate components
        self.validate_components(components)
        
        # Show what we're syncing
        
        # Display flags to be synced
        table_data = []
        for flag_name, flag_data in flags_config['flags'].items():
            table_data.append({
                'flag_name': flag_name,
                'enabled': "✓ True" if flag_data['enabled'] else "✗ False",
                'description': flag_data['description']
            })
        
        table = self.console_utils.create_list_table(
            table_data,
            title=f"Feature Flags to sync",
            columns=['flag_name', 'enabled', 'description']
        )
        self.console.print(table)
        self.console.print(f"\n[bold]Target components:[/bold] {', '.join(components)}\n")
        
        # Sync to each component
        results = []
        with self.console_utils.get_progress(f"Syncing to {len(components)} components...") as progress:
            task = progress.add_task("Syncing...", total=len(components))
            
            for component in components:
                try:
                    # Get auth method
                    auth_method, auth_client_or_token = self.get_auth_method(component, stage, auth_type)
                    
                    yaml_content = yaml.dump(flags_config)
                    
                    if auth_method == "direct":
                        # Use direct invoke
                        client = auth_client_or_token
                        response_data = client.post(
                            "/admin/flags",
                            headers={"Content-Type": "application/x-yaml"},
                            data=yaml_content
                        )
                        # Create response object
                        class Response:
                            def __init__(self, data):
                                self.status_code = data.get('statusCode', 500)
                                self._body = data.get('body', '{}')
                            def json(self):
                                return json.loads(self._body)
                            @property
                            def text(self):
                                return self._body
                        response = Response(response_data)
                    else:
                        # Use OIDC with HTTP
                        api_url = self.get_api_url(component, stage)
                        token = auth_client_or_token
                        
                        headers = {
                            "Authorization": token,
                            "Content-Type": "application/x-yaml"
                        }
                        
                        if "OIDC_USER_JWT" in token:
                            client_id = JWTUtils.extract_client_id(token)
                            if client_id:
                                headers["X-Client-ID"] = client_id
                        
                        response = requests.post(
                            f"{api_url}/admin/flags",
                            headers=headers,
                            data=yaml_content,
                            timeout=30
                        )
                    
                    success = response.status_code == 200
                    if success:
                        result_data = response.json()
                        self.console_utils.print_success(
                            f"{component}: Updated {result_data.get('updated_count', 0)} flags"
                        )
                    else:
                        self.console_utils.print_error(
                            f"{component}: Failed ({response.status_code}) - {response.text}"
                        )
                    
                    results.append((component, success))
                    
                except Exception as e:
                    self.console_utils.print_error(f"{component}: Error - {str(e)}")
                    results.append((component, False))
                
                progress.update(task, advance=1)
        
        # Display summary
        self.display_results(results, "Sync Summary")
    
    def set_flag(self, stage: str, flag_name: str, value: bool, reason: str, 
                 components: List[str], auth_type: Optional[str]):
        """Set a specific flag value across components."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        # Components are now required from the command
        
        # Validate components
        self.validate_components(components)
        
        # Display what we're doing
        status_data = {
            "Stage": stage,
            "Flag": flag_name,
            "Value": str(value),
            "Reason": reason,
            "Components": ", ".join(components)
        }
        
        table = self.console_utils.create_status_table("Setting Flag", status_data)
        self.console.print(table)
        
        # Update each component
        results = []
        for component in components:
            try:
                # Get auth method
                auth_method, auth_client_or_token = self.get_auth_method(component, stage, auth_type)
                
                # Build data
                data = {
                    "flag_name": flag_name,
                    "enabled": value,
                    "reason": reason
                }
                
                if auth_method == "direct":
                    # Use direct invoke
                    client = auth_client_or_token
                    response_data = client.put(
                        f"/admin/flags/{flag_name}",
                        headers={"Content-Type": "application/json"},
                        json_data=data
                    )
                    # Create response object
                    class Response:
                        def __init__(self, data):
                            self.status_code = data.get('statusCode', 500)
                            self._body = data.get('body', '{}')
                        def json(self):
                            return json.loads(self._body)
                        @property
                        def text(self):
                            return self._body
                    response = Response(response_data)
                else:
                    # Use OIDC with HTTP
                    api_url = self.get_api_url(component, stage)
                    token = auth_client_or_token
                    
                    headers = {"Authorization": token, "Content-Type": "application/json"}
                    
                    if "OIDC_USER_JWT" in token:
                        client_id = JWTUtils.extract_client_id(token)
                        if client_id:
                            headers["X-Client-ID"] = client_id
                    
                    response = requests.put(
                        f"{api_url}/admin/flags/{flag_name}",
                        headers=headers,
                        json=data,
                        timeout=30
                    )
                
                success = response.status_code == 200
                if success:
                    self.console_utils.print_success(f"{component}: Flag updated")
                else:
                    self.console_utils.print_error(
                        f"{component}: Failed ({response.status_code}) - {response.text}"
                    )
                
                results.append((component, success))
                
            except Exception as e:
                self.console_utils.print_error(f"{component}: Error - {str(e)}")
                results.append((component, False))
        
        # Display summary
        self.display_results(results, "Update Summary")
    
    def get_flags(self, stage: str, flag_name: Optional[str], 
                  components: List[str], auth_type: Optional[str]):
        """Get flag values from components."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        # Components are now required from the command
        
        # Validate components
        self.validate_components(components)
        
        self.console.print(f"\n[bold]Getting feature flags from {stage}:[/bold]\n")
        
        for component in components:
            try:
                # Get auth method
                auth_method, auth_client_or_token = self.get_auth_method(component, stage, auth_type)
                
                if auth_method == "direct":
                    # Use direct invoke
                    client = auth_client_or_token
                    path = f"/admin/flags"
                    if flag_name:
                        path += f"/{flag_name}"
                    
                    response_data = client.get(path)
                    # Create response object
                    class Response:
                        def __init__(self, data):
                            self.status_code = data.get('statusCode', 500)
                            self._body = data.get('body', '{}')
                        def json(self):
                            return json.loads(self._body)
                        @property
                        def text(self):
                            return self._body
                    response = Response(response_data)
                else:
                    # Use OIDC with HTTP
                    api_url = self.get_api_url(component, stage)
                    token = auth_client_or_token
                    
                    headers = {"Authorization": token}
                    
                    if "OIDC_USER_JWT" in token:
                        client_id = JWTUtils.extract_client_id(token)
                        if client_id:
                            headers["X-Client-ID"] = client_id
                    
                    # Get flags
                    url = f"{api_url}/admin/flags"
                    if flag_name:
                        url += f"/{flag_name}"
                    
                    response = requests.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if flag_name:
                        # Single flag
                        self.console.print(f"\n[bold]{component}:[/bold]")
                        self.console.print(f"  {flag_name}: {data.get('enabled', 'Not found')}")
                    else:
                        # All flags
                        flags = data.get('flags', [])
                        if flags:
                            table_data = []
                            for flag in flags:
                                table_data.append({
                                    'flag_name': flag.get('flag_name', 'Unknown'),
                                    'enabled': "✓ True" if flag.get('enabled') else "✗ False",
                                    'updated_by': flag.get('updated_by', 'Unknown'),
                                    'updated_at': flag.get('updated_at', 'Unknown')[:19]  # Trim timestamp
                                })
                            
                            table = self.console_utils.create_list_table(
                                table_data,
                                title=f"{component} - Feature Flags",
                                columns=['flag_name', 'enabled', 'updated_by', 'updated_at']
                            )
                            self.console.print(table)
                        else:
                            self.console_utils.print_warning(f"{component}: No flags found")
                else:
                    self.console_utils.print_error(
                        f"{component}: Failed to get flags ({response.status_code}) - {response.text}"
                    )
                    
            except Exception as e:
                self.console_utils.print_error(f"{component}: Error - {str(e)}")
    
    def list_flags(self):
        """List all available feature flags from flags.yml."""
        flags_config = self.load_flags_config()
        
        table_data = []
        for flag_name, flag_data in flags_config['flags'].items():
            table_data.append({
                'flag_name': flag_name,
                'default': "✓ True" if flag_data['enabled'] else "✗ False",
                'description': flag_data['description']
            })
        
        table = self.console_utils.create_list_table(
            table_data,
            title="Available Feature Flags",
            columns=['flag_name', 'default', 'description']
        )
        self.console.print(table)
        self.console.print(f"\n[dim]Configuration file: {self.flags_file}[/dim]")
    


def main():
    """Main entry point."""
    cli = FeatureFlagsCLI()
    cli.run()


if __name__ == "__main__":
    main()