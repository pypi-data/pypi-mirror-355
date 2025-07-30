#!/usr/bin/env python3
"""
Minimal OIDC registration CLI - Refactored modular version.
Automates client registration, secret storage, and API configuration.
"""
from pathlib import Path
import typer
from typing import Optional

# Add utils to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, ConfigUtils, ConsoleUtils, AppConfig

# Import OIDC modules
from oidc.prerequisites import PrerequisitesStep
from oidc.provider_registration import ProviderRegistrationStep
from oidc.credential_storage import CredentialStorageStep
from oidc.frontend_config import FrontendConfigStep
from oidc.api_registration import ApiRegistrationStep
from oidc.client_redirect import ClientRedirectStep
from oidc.cleanup import CleanupStep
from oidc.verification import VerificationStep
from oidc.orchestrator import OIDCOrchestrator


class OIDCCLI(BaseCLI):
    """Minimal OIDC registration CLI."""
    
    def __init__(self):
        # Initialize typer app directly to avoid base CLI auto-commands
        self.app = typer.Typer(
            name="oidc",
            help="OIDC client registration and management",
            rich_markup_mode="rich"
        )
        
        # Initialize console utils
        from utils import ConsoleUtils
        self.console_utils = ConsoleUtils()
        self.console = self.console_utils.console
        
        # Initialize step modules
        self.prerequisites = PrerequisitesStep()
        self.provider_registration = ProviderRegistrationStep()
        self.credential_storage = CredentialStorageStep()
        self.frontend_config = FrontendConfigStep()
        self.api_registration = ApiRegistrationStep()
        self.client_redirect = ClientRedirectStep()
        self.cleanup = CleanupStep()
        self.verification = VerificationStep()
        
        # Initialize orchestrator
        self.orchestrator = OIDCOrchestrator(
            self.prerequisites, self.provider_registration, self.credential_storage,
            self.frontend_config, self.api_registration, self.client_redirect,
            self.cleanup, self.verification
        )
        
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.command()
        def register(
            app: str = typer.Option(..., "--app", help="Application to register: legislative-review or oidc-manager"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", help="Developer initials to use (overrides config)"),
        ):
            """Register OIDC client for specified application."""
            # Set developer initials override if provided
            if developer_initials:
                AppConfig.set_developer_initials_override(developer_initials)
            
            # Validate app name
            valid_apps = ["legislative-review", "oidc-manager"]
            if app not in valid_apps:
                self.console_utils.print_error(
                    f"Invalid application: {app}\n"
                    f"Valid applications: {', '.join(valid_apps)}"
                )
                raise typer.Exit(1)
            
            # Check prerequisites
            if not self.prerequisites.check_system_prerequisites(require_docker=False, require_aws=True):
                raise typer.Exit(1)
            
            try:
                # Always pass app_context to bypass directory checks completely
                self.orchestrator.register_single_app(app, app_context=app)
                # Explicit success exit
                raise typer.Exit(0)
            except typer.Exit:
                # Re-raise typer exits without modification
                raise
            except Exception as e:
                self.console_utils.print_error(f"Registration failed: {e}")
                raise typer.Exit(1)
        
        
        @self.app.command()
        def verify_apis(
        ):
            """Verify API Gateway discovery and show detailed information."""
            # Check prerequisites
            if not self.prerequisites.check_system_prerequisites(require_docker=False, require_aws=True):
                raise typer.Exit(1)
            
            from utils import AWSUtils
            self.console.print(f"\n[bold cyan]🔍 API Gateway Discovery Verification[/bold cyan]")
            # Use new method to get API IDs from TOML
            from utils import APIGatewayUtils
            api_gateway_ids = APIGatewayUtils.get_all_api_gateway_ids("sandbox")
            
            # Print results
            self.console.print(f"\n[bold]API Gateway IDs from Configuration:[/bold]")
            for api_name, api_id in api_gateway_ids.items():
                self.console.print(f"  • {api_name}: {api_id}")
            
            if not api_gateway_ids:
                self.console.print("[red]No API Gateway IDs found in configuration![/red]")
            else:
                self.console.print(f"\nFound {len(api_gateway_ids)} API Gateway IDs")


def main():
    """Main entry point for the OIDC CLI."""
    cli = OIDCCLI()
    cli.app()


if __name__ == "__main__":
    main()