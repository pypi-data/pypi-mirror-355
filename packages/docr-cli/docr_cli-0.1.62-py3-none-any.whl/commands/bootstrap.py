#!/usr/bin/env python3
"""
Unified bootstrap CLI for all applications.
Located in legislative-review-backend as it's the main app.

Bootstrap Architecture:
- endpoint: Specifies which API/service to send bootstrap data to (legislative-review, workspaces)
- appkey: Tenant identifier that segregates data within each service (e.g., "legislative-review")
- Bootstrap files:
  - application.yml: Used when bootstrapping the main application endpoint
  - {endpoint}.yml: Used when bootstrapping component endpoints (workspaces.yml)

Authentication:
- Direct Invoke: Default for sandbox environments. Uses AWS Lambda direct invocation.
- OIDC (OpenID Connect): Default for dev/qa/prod. Uses JWT tokens from browser login.
- Override with --auth-type flag: 'direct' or 'oidc'

Example usage:
- Bootstrap main app: bootstrap --endpoint legislative-review --app legislative-review
  (Sends application.yml to legislative-review API, data segregated under "legislative-review")
  
- Bootstrap workspace component: bootstrap --endpoint workspaces --app legislative-review  
  (Sends workspaces.yml to workspaces API, data segregated under "legislative-review")
  
- Force OIDC auth in sandbox: bootstrap --endpoint workspaces --auth-type oidc
  
- Use direct invoke in dev: bootstrap --endpoint workspaces --stage dev --auth-type direct
"""
import os
import json
import requests
import yaml
import subprocess
import platform
import logging
from pathlib import Path
from typing import Optional, Any
import typer
from rich.table import Table
from loguru import logger

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import BaseCLI, ConfigUtils, JWTUtils, DirectInvokeClient
from commands.refresh import refresh_config

# Default app key for all components when bootstrapping


class BootstrapCLI(BaseCLI):
    """Bootstrap management CLI for workspace applications."""
    
    def __init__(self):
        super().__init__(
            name="bootstrap",
            help_text="Bootstrap data management for applications and components.\n\n"
                     "Sends YAML configuration to different API endpoints to initialize data.\n"
                     "The endpoint determines which service receives the data,\n"
                     "while appkey provides tenant isolation within that service.",
            require_config=False,  # Bootstrap might run without full config
            setup_python_path=False  # Don't require config for setup
        )
        
        # Token files will be stage-specific
        self.ssh_dir = Path.home() / ".ssh"
        self.ssh_dir.mkdir(exist_ok=True)
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.callback(invoke_without_command=True)
        def bootstrap(
            ctx: typer.Context,
            endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="API endpoint to send bootstrap data to (legislative-review, workspaces). Required when not using subcommands."),
            app: Optional[str] = typer.Option(None, "--app", "-a", help="Application identifier for data segregation (e.g., legislative-review). Required for all operations."),
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage"),
            auth_type: str = typer.Option(None, "--auth-type", "-u", help="Authentication type: 'oidc' or 'direct' (defaults to direct for sandbox, oidc for dev/qa/prod)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
        ):
            """Bootstrap application or component with configuration data.
            
            Works from any directory - no need to be in a specific location.
            
            \b
            Examples:
              Bootstrap main application:
                docr bootstrap --endpoint legislative-review --app legislative-review
                
              Bootstrap workspace component:
                docr bootstrap --endpoint workspaces --app legislative-review
                
              Bootstrap all components:
                docr bootstrap all --app legislative-review
                
              Use OIDC auth in sandbox:
                docr bootstrap --endpoint workspaces --app legislative-review --auth-type oidc
                
              Use direct invoke in dev:
                docr bootstrap --endpoint workspaces --app legislative-review --stage dev --auth-type direct
            """
            # Set developer initials override if provided
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            
            # If a subcommand was invoked, don't run the main bootstrap logic
            if ctx.invoked_subcommand is not None:
                return
            
            # For direct bootstrap (no subcommand), both endpoint and app are required
            if not endpoint:
                self.console_utils.print_error("Missing required option '--endpoint' / '-e'")
                self.console.print("\nFor bootstrapping all components, use: docr bootstrap all --app <app-name>")
                raise typer.Exit(1)
            
            if not app:
                self.console_utils.print_error("Missing required option '--app' / '-a'")
                raise typer.Exit(1)
            
            if not verbose:
                self._suppress_logging()
            
            # Run bootstrap with provided parameters
            self.run_bootstrap(endpoint, app, None, stage, auth_type)
        
        @self.app.command()
        def clear(
            endpoint: Optional[str] = typer.Option(None, "--endpoint", "-e", help="Specific endpoint to clear (legislative-review, workspaces). If not specified, clears ALL endpoints."),
            app: str = typer.Option(..., "--app", "-a", help="Application identifier for data to clear (required)"),
            confirm: bool = typer.Option(False, "--confirm", help="Confirm deletion"),
            force: bool = typer.Option(False, "--force", "-f", help="Skip confirmation prompt"),
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage"),
            auth_type: str = typer.Option(None, "--auth-type", "-u", help="Authentication type: 'oidc' or 'direct' (defaults to direct for sandbox, oidc for dev/qa/prod)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
        ):
            """Clear bootstrap data (DANGEROUS!).
            
            If endpoint is specified: Clears data for the app from that specific endpoint.
            If endpoint is not specified: Clears data for the app from ALL endpoints.
            """
            # Set developer initials override if provided
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            
            if not verbose:
                self._suppress_logging()
            
            # Handle endpoint specification
            if endpoint:
                # User specified an endpoint explicitly
                self.clear_bootstrap(endpoint, app, confirm, force, stage, auth_type)
            else:
                # No endpoint specified - always clear ALL endpoints
                self.clear_all_endpoints(app, confirm, force, stage, auth_type)
        
        @self.app.command()
        def all(
            app: str = typer.Option(..., "--app", "-a", help="Application identifier (e.g., legislative-review) (required)"),
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage"),
            auth_type: str = typer.Option(None, "--auth-type", "-u", help="Authentication type: 'oidc' or 'direct' (defaults to direct for sandbox, oidc for dev/qa/prod)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
        ):
            """Bootstrap all components in the correct order."""
            # Set developer initials override if provided
            if developer_initials:
                from utils import AppConfig
                AppConfig.set_developer_initials_override(developer_initials)
            
            if not verbose:
                self._suppress_logging()
            self.bootstrap_all(app, stage, auth_type, verbose)
        
        
        # Create token subcommand group
        token_app = typer.Typer(help="Manage OIDC authentication token (not used for direct invoke auth)")
        self.app.add_typer(token_app, name="token")
        
        @token_app.command("show")
        def token_show(
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage")
        ):
            """Display information about the saved OIDC token."""
            self.show_token_info(stage)
        
        @token_app.command("clear")
        def token_clear(
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage")
        ):
            """Clear the saved OIDC token."""
            self.clear_token(stage)
        
        @token_app.command("refresh")
        def token_refresh(
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage")
        ):
            """Get a new OIDC token."""
            self.refresh_token(stage)
        
        @token_app.command("edit")
        def token_edit(
            stage: str = typer.Option("sandbox", "--stage", "-s", help="Environment stage")
        ):
            """Open the token file in system editor."""
            self.edit_token(stage)
    
    def _suppress_logging(self):
        """Suppress all logging output when verbose is False."""
        # Suppress loguru logger
        logger.remove()  # Remove default handler
        logger.add(lambda msg: None)  # Add null handler to suppress all logs
        
        # Suppress boto3 and botocore logging
        logging.getLogger('boto3').setLevel(logging.CRITICAL)
        logging.getLogger('botocore').setLevel(logging.CRITICAL)
        logging.getLogger('urllib3').setLevel(logging.CRITICAL)
        
        # Suppress other common noisy loggers
        logging.getLogger('s3transfer').setLevel(logging.CRITICAL)
        logging.getLogger('credentials').setLevel(logging.CRITICAL)
    
    def get_api_url(self, endpoint: str, stage: str) -> str:
        """Get the API URL for a specific endpoint."""
        from utils.api_utils import get_api_url_for_service
        return get_api_url_for_service(
            endpoint, 
            self.console_utils,
            stage=stage,
            show_info=True,
            show_supported_endpoints=True
        )
    
    def get_direct_invoke_client(self, endpoint: str, stage: str = "sandbox") -> DirectInvokeClient:
        """Get direct invoke client for the specified endpoint."""
        try:
            self.console_utils.print_success(f"Using direct invoke for endpoint '{endpoint}'")
            return DirectInvokeClient(endpoint, stage)
        except Exception as e:
            self.console_utils.print_error(f"Failed to create direct invoke client: {str(e)}", exit_code=1)
    
    def get_oidc_token(self, stage: str = "sandbox") -> str:
        """Get OIDC user token from saved file."""
        # Use stage-specific token file
        token_file = self.ssh_dir / f"docr.oidc.token.{stage}.txt"
        
        # Check if we have a saved token
        if token_file.exists():
            with open(token_file, 'r', encoding='utf-8') as f:
                saved_token = f.read().strip()
            
            # Validate token format
            if JWTUtils.validate_token_format(saved_token):
                # Check expiry
                is_valid, time_remaining = JWTUtils.check_expiry(saved_token)
                
                if is_valid:
                    time_str = JWTUtils.format_time_remaining(time_remaining)
                    self.console_utils.print_success(f"Using saved token (expires in {time_str})")
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
        self.console.print(f"[cyan]echo 'YOUR_FULL_TOKEN_HERE' > ~/.ssh/docr.oidc.token.{stage}.txt[/cyan]")
        self.console.print("\n[bold]Or use the bootstrap token commands:[/bold]")
        self.console.print("[cyan]bootstrap token edit[/cyan]     # Open token file in editor")
        self.console.print("[cyan]bootstrap token clear[/cyan]    # Remove old/invalid token")
        self.console.print("[cyan]bootstrap token refresh[/cyan]  # Get a new token")
        self.console.print("\nThe token is valid for 1 hour after login.")
        
        raise typer.Exit(1)
    
    def get_auth_method(self, endpoint: str, stage: str, auth_type: Optional[str] = None) -> tuple[str, Any]:
        """Get authentication method based on stage and auth type.
        
        Args:
            endpoint: The API endpoint being accessed
            stage: The deployment stage (sandbox, dev, qa, prod)
            auth_type: Override auth type ('direct' or 'oidc')
            
        Returns:
            Tuple of (auth_type, auth_client_or_token)
        """
        # Determine auth type based on stage if not explicitly provided
        if auth_type is None:
            # Default to direct invoke for sandbox, OIDC for other stages
            auth_type = "direct" if stage == "sandbox" else "oidc"
        
        # Validate auth type
        if auth_type not in ["direct", "oidc"]:
            self.console_utils.print_error(f"Invalid auth type '{auth_type}'. Must be 'direct' or 'oidc'.", exit_code=1)
        
        # Get appropriate auth method
        if auth_type == "direct":
            return "direct", self.get_direct_invoke_client(endpoint, stage)
        else:
            return "oidc", self.get_oidc_token(stage)
    
    
    def get_bootstrap_file_path(self, endpoint: str, stage: str, appkey: str = None) -> Path:
        """Get the path to a bootstrap file for a specific endpoint.
        
        For the main application endpoint (legislative-review), uses application.yml.
        For component endpoints (workspaces), uses {endpoint}.yml.
        """
        # Determine which bootstrap file to use based on endpoint
        from utils import AppConfig
        
        # DEBUG: Print all path resolution details
        self.console_utils.print_info("\n=== Bootstrap Path Resolution Debug ===")
        self.console_utils.print_info(f"Endpoint: {endpoint}")
        self.console_utils.print_info(f"Stage: {stage}")
        self.console_utils.print_info(f"App Key: {appkey}")
        
        # Debug project root
        project_root = AppConfig.get_project_root()
        self.console_utils.print_info(f"Project Root: {project_root}")
        
        if AppConfig.is_application(endpoint):
            # Main application uses application.yml
            file_name = "application"
        else:
            # Components use their own yml files
            file_name = endpoint
        
        self.console_utils.print_info(f"File Name: {file_name}.yml")
        
        # Use appkey to determine which app's config directory to use
        # If appkey is not provided, try to determine from endpoint
        if appkey:
            app_name = appkey
        elif AppConfig.is_application(endpoint):
            app_name = endpoint
        else:
            # For components without appkey, we can't determine the app
            raise ValueError(
                f"Cannot determine application for component '{endpoint}'. "
                f"Please specify --app parameter."
            )
        
        self.console_utils.print_info(f"App Name: {app_name}")
        
        # Debug backend directory resolution
        try:
            backend_dir = AppConfig.get_app_backend_dir(app_name)
            self.console_utils.print_info(f"Backend Dir: {backend_dir}")
            
            # Debug backend path from config
            from utils.path_config import PathConfig
            from utils.project_config import ProjectConfig
            config_data = AppConfig._get_project_config().config_data
            backend_path = config_data.get('applications', {}).get(app_name, {}).get('backend_path', 'NOT FOUND')
            self.console_utils.print_info(f"Backend Path from Config: {backend_path}")
        except Exception as e:
            self.console_utils.print_error(f"Error getting backend dir: {e}")
        
        # Debug config directory
        config_dir = AppConfig.get_config_dir(app_name)
        self.console_utils.print_info(f"Config Dir: {config_dir}")
        
        bootstrap_dir = config_dir / "bootstrap" / stage
        self.console_utils.print_info(f"Bootstrap Dir: {bootstrap_dir}")
        
        bootstrap_file = bootstrap_dir / f"{file_name}.yml"
        self.console_utils.print_info(f"Bootstrap File: {bootstrap_file}")
        self.console_utils.print_info(f"File Exists: {bootstrap_file.exists()}")
        
        # List contents of bootstrap directory if it exists
        if bootstrap_dir.exists():
            self.console_utils.print_info(f"Contents of {bootstrap_dir}:")
            for item in bootstrap_dir.iterdir():
                self.console_utils.print_info(f"  - {item.name}")
        else:
            self.console_utils.print_warning(f"Bootstrap directory does not exist: {bootstrap_dir}")
        
        self.console_utils.print_info("=== End Debug ===\n")
        
        if not bootstrap_file.exists():
            self.console_utils.print_warning(f"Bootstrap file not found: {bootstrap_file}")
            # Try to find example file
            example_file = bootstrap_dir / f"{file_name}.example.yml"
            if example_file.exists():
                self.console_utils.print_info(f"Using example file: {example_file}")
                return example_file
            else:
                raise FileNotFoundError(f"Bootstrap file not found: {bootstrap_file}")
        
        return bootstrap_file
    
    def run_bootstrap(self, endpoint: str, appkey: str, config_file: Optional[Path], 
                     stage: str, auth_type: Optional[str] = None):
        """Bootstrap an application with configuration."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        # Get authentication method
        auth_method, auth_client_or_token = self.get_auth_method(endpoint, stage, auth_type)
        
        # For OIDC, get API URL and extract client ID
        client_id = None
        if auth_method == "oidc":
            api_url = self.get_api_url(endpoint, stage)
            token = auth_client_or_token
            if "OIDC_USER_JWT" in token:
                client_id = JWTUtils.extract_client_id(token)
                if not client_id:
                    self.console_utils.print_warning("Could not extract client ID from OIDC token")
        
        with self.console_utils.get_progress(f"Bootstrapping {endpoint} endpoint with app {appkey}...") as progress:
            task = progress.add_task("Processing...", total=None)
            
            
            # Load bootstrap file
            if config_file:
                bootstrap_file = config_file
            else:
                bootstrap_file = self.get_bootstrap_file_path(endpoint, stage, appkey)
            
            if not bootstrap_file.exists():
                self.console_utils.print_error(f"Bootstrap file not found: {bootstrap_file}", exit_code=1)
            
            self.console_utils.print_info(f"Using bootstrap file: {bootstrap_file}")
            
            # Read and validate YAML
            with open(bootstrap_file) as f:
                yaml_content = f.read()
                try:
                    yaml.safe_load(yaml_content)
                except yaml.YAMLError as e:
                    self.console_utils.print_error(f"Invalid YAML: {e}", exit_code=1)
            
            # Call API with YAML content
            if auth_method == "direct":
                # Use direct invoke
                client = auth_client_or_token
                response_data = client.post(
                    f"/admin/bootstrap/{appkey}",
                    headers={"Content-Type": "application/x-yaml"},
                    data=yaml_content
                )
                # Create a response-like object for consistency
                class DirectResponse:
                    def __init__(self, data):
                        self.status_code = data.get('statusCode', 500)
                        self._body = data.get('body', '{}')
                    def json(self):
                        return json.loads(self._body)
                    @property
                    def text(self):
                        return self._body
                response = DirectResponse(response_data)
            else:
                # Use OIDC with HTTP
                post_headers = {
                    "Authorization": token,
                    "Content-Type": "application/x-yaml"
                }
                if client_id:
                    post_headers["X-Client-ID"] = client_id
                
                response = requests.post(
                    f"{api_url}/admin/bootstrap/{appkey}",
                    headers=post_headers,
                    data=yaml_content
                )
            progress.update(task, completed=True)
        
        if response.status_code == 403:
            self.console_utils.print_error(
                f"Access denied. Requires {appkey}:admins entitlement",
                exit_code=1
            )
        
        if response.status_code != 200:
            self.console_utils.print_error(f"Error: {response.text}", exit_code=1)
        
        # Display results
        result = response.json()
        status_color = "green" if result["status"] == "success" else "red"
        self.console.print(f"\n[{status_color}]{result['status'].upper()}[/{status_color}]: {result['message']}")
        
        if operations := result.get("operations"):
            table = Table(title="Operations")
            table.add_column("Status", style="cyan")
            table.add_column("Operation")
            table.add_column("Message")
            
            for op in operations:
                status = "✅" if op["success"] else "❌"
                table.add_row(status, op["operation"], op["message"])
            
            self.console.print(table)
    
    def clear_bootstrap(self, endpoint: str, appkey: str, confirm: bool, 
                       force: bool, stage: str, auth_type: Optional[str] = None):
        """Clear all bootstrap data for an application."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        # Get authentication method
        auth_method, auth_client_or_token = self.get_auth_method(endpoint, stage, auth_type)
        
        # For OIDC, get API URL
        if auth_method == "oidc":
            api_url = self.get_api_url(endpoint, stage)
            token = auth_client_or_token
        
        if not force and not confirm:
            really = self.console_utils.prompt_confirm(
                f"⚠️  This will DELETE ALL DATA for app '{appkey}' in endpoint '{endpoint}'. Are you sure?",
                default=False
            )
            if not really:
                self.console_utils.print_warning("Cancelled")
                raise typer.Exit()
        
        # Extract client ID from token (only for OIDC tokens)
        client_id = None
        if auth_method == "oidc" and "OIDC_USER_JWT" in token:
            client_id = JWTUtils.extract_client_id(token)
            if not client_id:
                self.console_utils.print_warning("Could not extract client ID from OIDC token")
        
        with self.console_utils.get_progress(f"Clearing data for app '{appkey}' in endpoint '{endpoint}'...") as progress:
            task = progress.add_task("Deleting...", total=None)
            
            if auth_method == "direct":
                # Use direct invoke
                client = auth_client_or_token
                response_data = client.delete(
                    f"/admin/bootstrap/{appkey}/data",
                    headers={"Content-Type": "application/json"},
                    json_data={"confirm": True}
                )
                # Create a response-like object for consistency
                class DirectResponse:
                    def __init__(self, data):
                        self.status_code = data.get('statusCode', 500)
                        self._body = data.get('body', '{}')
                    def json(self):
                        return json.loads(self._body)
                    @property
                    def text(self):
                        return self._body
                response = DirectResponse(response_data)
            else:
                # Use OIDC with HTTP
                headers = {
                    "Authorization": token,
                    "Content-Type": "application/json"
                }
                if client_id:
                    headers["X-Client-ID"] = client_id
                
                url = f"{api_url}/admin/bootstrap/{appkey}/data"
                
                response = requests.delete(
                    url,
                    headers=headers,
                    json={"confirm": True}
                )
            progress.update(task, completed=True)
        
        if response.status_code == 403:
            self.console_utils.print_error("Access denied (403)", exit_code=1)
        
        if response.status_code != 200:
            self.console_utils.print_error(f"Error ({response.status_code}): {response.text}", exit_code=1)
        
        result = response.json()
        self.console_utils.print_success(f"Cleared {result['deleted_count']} items from app '{appkey}'")
    
    def clear_all_endpoints(self, appkey: str, confirm: bool, force: bool, 
                           stage: str, auth_type: Optional[str] = None):
        """Clear bootstrap data from all endpoints."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        # Define all endpoints to clear
        from utils import AppConfig
        applications = AppConfig.discover_applications()
        bootstrap_enabled = AppConfig.get_bootstrap_enabled_components()
        all_endpoints = applications + bootstrap_enabled
        
        if not force and not confirm:
            really = self.console_utils.prompt_confirm(
                f"⚠️  This will DELETE ALL DATA for app '{appkey}' from ALL ENDPOINTS ({', '.join(all_endpoints)}). Are you sure?",
                default=False
            )
            if not really:
                self.console_utils.print_warning("Cancelled")
                raise typer.Exit()
        
        self.console.print(f"\n[bold]Clearing data for app '{appkey}' from all endpoints...[/bold]\n")
        
        # Track results
        results = []
        
        for endpoint in all_endpoints:
            try:
                self.console_utils.print_info(f"Clearing {endpoint}...")
                self.clear_bootstrap(endpoint, appkey, confirm=True, force=True, 
                                   stage=stage, auth_type=auth_type)
                results.append((endpoint, True, "Success"))
            except Exception as e:
                error_msg = str(e)
                results.append((endpoint, False, error_msg))
                self.console_utils.print_warning(f"Failed to clear {endpoint}: {error_msg}")
        
        # Show summary
        self.console.print("\n[bold]Clear Summary:[/bold]")
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Endpoint", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Message")
        
        for endpoint, success, message in results:
            status = "✅" if success else "❌"
            table.add_row(endpoint, status, message)
        
        self.console.print(table)
        
        # Summary counts
        success_count = sum(1 for _, success, _ in results if success)
        fail_count = len(results) - success_count
        
        if fail_count == 0:
            self.console_utils.print_success(f"Successfully cleared data from all {len(results)} endpoints")
        else:
            self.console_utils.print_warning(f"Cleared {success_count} endpoints, {fail_count} failed")
    
    def bootstrap_all(self, app: str, stage: str, auth_type: Optional[str] = None, verbose: bool = False):
        """Bootstrap all components in the correct order."""
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        self.console.print("[bold]Bootstrapping all components...[/bold]\n")
        
        # Show auth type being used
        resolved_auth_type = auth_type or ("direct" if stage == "sandbox" else "oidc")
        self.console_utils.print_info(f"Using {resolved_auth_type.upper()} authentication for stage '{stage}'")
        
        # Define bootstrap order - endpoint and appkey pairs
        from utils import AppConfig
        
        # App identifier is required and passed from the command
        
        # Build bootstrap order dynamically
        # Components that support bootstrap come first, then main application
        bootstrap_order = []
        for comp in AppConfig.get_bootstrap_enabled_components():
            bootstrap_order.append((comp, app))
        bootstrap_order.append((app, app))
        
        for endpoint, appkey in bootstrap_order:
            try:
                self.console_utils.print_step(
                    bootstrap_order.index((endpoint, appkey)) + 1,
                    len(bootstrap_order),
                    f"Bootstrapping {endpoint} endpoint"
                )
                self.run_bootstrap(endpoint, appkey, None, stage, auth_type)
            except Exception as e:
                self.console_utils.print_error(f"Failed to bootstrap {endpoint}: {e}")
                # Continue with other components even if one fails
    
    
    def clear_token(self, stage: str = "sandbox"):
        """Clear the saved OIDC token."""
        token_file = self.ssh_dir / f"docr.oidc.token.{stage}.txt"
        if token_file.exists():
            token_file.unlink()
            self.console_utils.print_success(f"OIDC token cleared from: {token_file}")
        else:
            self.console_utils.print_warning(f"No saved OIDC token found at: {token_file}")
    
    def refresh_token(self, stage: str = "sandbox"):
        """Get a new OIDC token."""
        # Force getting a new token by removing the old one
        token_file = self.ssh_dir / f"docr.oidc.token.{stage}.txt"
        if token_file.exists():
            token_file.unlink()
        self.get_oidc_token(stage)
        self.console_utils.print_success(f"Token refreshed successfully for {stage} stage")
    
    def edit_token(self, stage: str = "sandbox"):
        """Open the token file in system editor."""
        token_file = self.ssh_dir / f"docr.oidc.token.{stage}.txt"
        # Create token file if it doesn't exist
        if not token_file.exists():
            token_file.touch()
            self.console_utils.print_info(f"Created empty token file: {token_file}")
        
        # Determine the editor to use
        editor = os.environ.get('EDITOR')
        if not editor:
            # Use platform-specific defaults
            if platform.system() == 'Windows':
                editor = 'notepad'
            elif platform.system() == 'Darwin':  # macOS
                editor = 'nano'  # Use nano as it's more user-friendly than vi
            else:  # Linux and others
                editor = 'nano'
        
        try:
            self.console_utils.print_info(f"Opening {token_file} in {editor}...")
            subprocess.call([editor, str(token_file)])
        except Exception as e:
            self.console_utils.print_error(f"Failed to open editor: {e}")
            self.console.print(f"\nYou can manually edit the file at: {token_file}")
    
    def show_token_info(self, stage: str = "sandbox"):
        """Display information about the saved token."""
        token_file = self.ssh_dir / f"docr.oidc.token.{stage}.txt"
        if not token_file.exists():
            self.console_utils.print_warning(f"No saved token found for {stage} stage")
            self.console.print("\nRun any bootstrap command to be prompted for a token.")
            self.console.print(f"Or run: bootstrap token refresh --stage {stage}")
            return
        
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                saved_token = f.read().strip()
        except UnicodeDecodeError as e:
            self.console_utils.print_error(f"Token file is corrupted or not in UTF-8 format: {e}")
            self.console.print("\nThe token file appears to be corrupted. You can:")
            self.console.print(f"1. Clear it: bootstrap token clear --stage {stage}")
            self.console.print(f"2. Get a new token: bootstrap token refresh --stage {stage}")
            self.console.print(f"3. Edit it manually: bootstrap token edit --stage {stage}")
            return
        except Exception as e:
            self.console_utils.print_error(f"Error reading token file: {e}")
            return
        
        if not saved_token:
            self.console_utils.print_warning("Token file is empty")
            self.console.print(f"\nRun: bootstrap token refresh --stage {stage}")
            return
        
        if not JWTUtils.validate_token_format(saved_token):
            self.console_utils.print_error("Invalid token format")
            self.console.print("\nThe token should start with 'Bearer OIDC_USER_JWT:' followed by the JWT token.")
            self.console.print("You can:")
            self.console.print(f"1. Get a new token: bootstrap token refresh --stage {stage}")
            self.console.print(f"2. Edit the token: bootstrap token edit --stage {stage}")
            return
        
        # Display token info
        table = JWTUtils.format_token_info(saved_token)
        self.console.print(table)
        
        # Token length
        self.console.print(f"\n[bold]Token length:[/bold] {len(saved_token)} characters")


def main():
    """Main entry point."""
    cli = BootstrapCLI()
    cli.run()


if __name__ == "__main__":
    main()