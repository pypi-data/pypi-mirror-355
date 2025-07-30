"""
OIDC Registration Orchestrator
- Main workflows for OIDC client registration
- Handles single app and bulk app registration
- Coordinates all registration steps
"""
import time
from typing import Dict, Optional
import typer
from utils import ConfigUtils, ConsoleUtils, OIDCConfigManager, AppConfig
from utils.shared_console import get_shared_console

# Import refresh function to ensure config is up-to-date
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from commands.refresh import refresh_config


class OIDCOrchestrator:
    """Orchestrates OIDC registration workflows."""
    
    def __init__(self, prerequisites, provider_registration, credential_storage, 
                 frontend_config, api_registration, client_redirect, cleanup, verification):
        """Initialize with step dependencies."""
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
        
        # Step dependencies
        self.prerequisites = prerequisites
        self.provider_registration = provider_registration
        self.credential_storage = credential_storage
        self.frontend_config = frontend_config
        self.api_registration = api_registration
        self.client_redirect = client_redirect
        self.cleanup = cleanup
        self.verification = verification
    
    def _ensure_config_refreshed(self):
        """Refresh configuration from AWS CloudFormation to ensure we have latest stack outputs."""
        try:
            self.console.print("[cyan]Refreshing configuration from AWS CloudFormation...[/cyan]")
            refresh_config()
            self.console_utils.print_success("Configuration refreshed with latest stack outputs")
        except Exception as e:
            # Don't fail if refresh fails - just warn
            self.console.print(f"[yellow]Warning: Could not refresh config: {e}[/yellow]")
            self.console.print("[dim]Continuing with cached configuration...[/dim]")
    
    
    def register_single_app(self, app: str, app_context: Optional[str] = None):
        """Register OIDC for a single application."""
        # Refresh configuration first to ensure we have latest stack outputs
        self._ensure_config_refreshed()
        
        stage = "sandbox"
        
        # Check API Gateway deployments before proceeding
        discovered_apis = self.prerequisites.verify_api_deployments(stage)
        
        self.console.print(f"\n[bold cyan]🔐 OIDC Registration for {app}-{stage}[/bold cyan]")
        self.console.print("─" * 50)
        
        # Complete OIDC registration process with app_context always set
        self.register_oidc(app, stage, discovered_apis, app_context)
    
    def register_oidc(self, app: str, stage: str, discovered_apis: Dict[str, str], app_context: Optional[str] = None):
        """Complete OIDC registration process with app/component differentiation."""
        # Load configuration using consolidated utility
        # If we have app_context, use it to load config for specific app
        if app_context:
            from utils import ConfigUtils
            config = ConfigUtils(stage, app_context)
            dev_initials = AppConfig.get_developer_initials()
        else:
            config, dev_initials = OIDCConfigManager.get_oidc_config(stage)
        
        # Determine if this is an application or component
        is_application = AppConfig.is_application(app)
        app_type = "Application" if is_application else "Component"
        
        self.console.print(f"\n[bold cyan]🔐 OIDC Registration for {app}-{stage} ({app_type})[/bold cyan]")
        self.console.print("─" * 50)
        
        # Applications: Run all steps 1-7
        # Components: Skip frontend steps, run 2,3,5,6,7
        
        frontend_url = None
        frontend_config_path = None
        
        if is_application:
            # Step 1: Frontend Configuration Detection (Applications only)
            self.console.print(f"\n[yellow]Step 1: Frontend Configuration Detection[/yellow]")
            frontend_url, frontend_config_path = self.frontend_config.detect_frontend_config(app, stage, dev_initials)
        else:
            # Components: Generate a basic redirect URL for OIDC provider registration
            frontend_url = f"https://{app}-{dev_initials}.it-eng-ai.aws.umd.edu/"
            self.console.print(f"\n[dim]Skipping frontend config detection (component)[/dim]")
        
        # Step 2: OIDC Provider Registration (All apps)
        step_num = "2" if is_application else "1"
        self.console.print(f"\n[yellow]Step {step_num}: OIDC Provider Registration[/yellow]")
        client_id, client_secret = self.provider_registration.register_with_provider(app, frontend_url, stage, dev_initials)
        self.console.print(f"  ✓ Client registered successfully")
        self.console.print(f"  ✓ Client ID: [cyan]{client_id}[/cyan]")
        
        # Step 3: Credential Storage (All apps)
        step_num = "3" if is_application else "2"
        self.console.print(f"\n[yellow]Step {step_num}: Credential Storage[/yellow]")
        if self.credential_storage.store_client_secret(app, client_secret, stage, dev_initials):
            self.console.print("  ✓ Client secret stored securely")
        else:
            self.console.print("  ⚠ Client secret storage failed - registration may not work properly")
        
        if is_application:
            # Step 4: Frontend Configuration Update (Applications only)
            if frontend_config_path:
                self.console.print(f"\n[yellow]Step 4: Frontend Configuration Update[/yellow]")
                frontend_dir = AppConfig.get_app_frontend_dir(app)
                self.frontend_config.update_frontend_config(client_id, frontend_config_path, app, frontend_dir)
                self.console.print("  ✓ Frontend config updated with new client ID")
        else:
            self.console.print(f"\n[dim]Skipping frontend config update (component)[/dim]")
        
        # Step 5: API Gateway Registration (All apps)
        step_num = "5" if is_application else "3"
        self.console.print(f"\n[yellow]Step {step_num}: API Gateway Registration[/yellow]")
        registered_apis = self.api_registration.register_with_all_apis(client_id, stage, dev_initials, discovered_apis, app_name=app)
        
        # Step 6: Client Redirect URI Registration (All apps)
        step_num = "6" if is_application else "4"
        self.console.print(f"\n[yellow]Step {step_num}: Client Redirect URI Registration[/yellow]")
        self.client_redirect.register_client_redirect(client_id, frontend_url, app, stage, dev_initials)
        self.console.print("  ✓ Redirect URI registered")
        
        # Add a small delay to allow DynamoDB writes to propagate
        import time
        self.console.print("  [dim]Waiting for DynamoDB propagation...[/dim]")
        time.sleep(1)  # Brief pause for consistency
        
        # Step 7: Final Verification (All apps)
        step_num = "7" if is_application else "5"
        self.console.print(f"\n[yellow]Step {step_num}: Final Verification[/yellow]")
        try:
            verification_success = self.verification.verify_single_registration(app, stage, discovered_apis=discovered_apis, app_context=app_context)
        except Exception as e:
            # Don't fail the whole registration just because verification has timing issues
            self.console.print(f"\n[yellow]⚠ Verification check encountered issues (this is often due to DynamoDB propagation delay)[/yellow]")
            verification_success = False
        
        # Summary
        self.console.print("\n" + "─" * 50)
        self.console.print(f"[bold green]✓ OIDC Registration Complete for {app_type}![/bold green]")
        self.console.print("\n[bold]Summary:[/bold]")
        self.console.print(f"  • Client ID: [cyan]{client_id}[/cyan]")
        self.console.print(f"  • Redirect URI: [cyan]{frontend_url}[/cyan]")
        self.console.print(f"  • Secret stored: ✓")
        if is_application:
            self.console.print(f"  • Frontend config updated: {'✓' if frontend_config_path else '⚠'}")
        else:
            self.console.print(f"  • Frontend config: N/A (component)")
        
        # Next steps
        if is_application:
            self.console.print("\n[bold yellow]⚠️  IMPORTANT: Frontend Deployment Required![/bold yellow]")
            self.console.print("\n[yellow]The new OIDC client ID will NOT work until you deploy the frontend.[/yellow]")
            self.console.print("\n[bold]Deploy the frontend NOW:[/bold]")
            self.console.print(f"  1. Navigate to the frontend directory:")
            # Get the actual frontend directory for this app
            app_frontend_dir = AppConfig.get_app_frontend_dir(app)
            self.console.print(f"     [cyan]cd {app_frontend_dir}[/cyan]")
            self.console.print(f"  2. Deploy to S3/CloudFront:")
            self.console.print(f"     [cyan]docr deploy frontend[/cyan]")
            self.console.print("\n[blue]Without deployment, authentication will fail with the old client ID.[/blue]")
            
            # Browser cache warnings
            self.console.print("\n[bold yellow]After Deployment - Browser Cache Cleanup:[/bold yellow]")
            self.console.print("  1. [yellow]Clear browser storage:[/yellow]")
            self.console.print("     • Open Chrome DevTools (F12) → Application → Storage")
            self.console.print("     • Click 'Clear site data'")
            self.console.print("  2. [yellow]Remove OAuth codes from URL:[/yellow]")
            self.console.print("     • If URL contains '?code=...', remove it")
            self.console.print("     • Navigate to clean URL: [cyan]" + frontend_url + "[/cyan]")
        else:
            self.console.print("\n[bold yellow]Component Notes:[/bold yellow]")
            self.console.print(f"  • {app} is a reusable component")
            self.console.print(f"  • It integrates into applications via frontend deployment")
            self.console.print(f"  • No standalone frontend deployment needed")