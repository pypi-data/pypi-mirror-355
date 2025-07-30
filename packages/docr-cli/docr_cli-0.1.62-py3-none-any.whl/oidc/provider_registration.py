"""
Step 2: OIDC Provider Registration
- Register client with OIDC provider
- Get client ID and secret
"""
import requests
import typer
from rich.console import Console
from utils import ConsoleUtils, AppConfig
from utils.shared_console import get_shared_console


class ProviderRegistrationStep:
    """Handle OIDC provider registration."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def register_with_provider(self, app: str, redirect_url: str, stage: str, dev_initials: str) -> tuple[str, str]:
        """Register with OIDC provider and get credentials."""
        # Get configuration
        authority = "https://shib.idm.dev.umd.edu"
        contact_email = "cmann@umd.edu"  # Default contact
        
        # Get the proper OIDC client name from app config
        oidc_client_name = AppConfig.get_oidc_client_name(app)
        client_name = f"{oidc_client_name}-{dev_initials}"
        
        registration_data = {
            "client_name": client_name,
            "redirect_uris": [redirect_url],
            "contacts": [contact_email],
            "response_types": ["code", "id_token"],
            "scope": "openid profile email entitlements"  # Keep as string, not array
        }
        
        self.console.print(f"  → Registering client '{client_name}' with {authority}")
        
        # Print what we're sending for debugging
        self.console.print(f"\n[cyan]🔍 VERBOSE: Registration Request Details[/cyan]")
        self.console.print(f"[cyan]URL:[/cyan] {authority}/shibboleth-idp/profile/oidc/register")
        self.console.print(f"[cyan]Method:[/cyan] POST")
        self.console.print(f"[cyan]Headers:[/cyan] Content-Type: application/json")
        self.console.print(f"[cyan]Payload:[/cyan]")
        import json
        self.console.print(json.dumps(registration_data, indent=2))
        
        # Call OIDC registration endpoint
        try:
            response = requests.post(
                f"{authority}/shibboleth-idp/profile/oidc/register",
                json=registration_data,
                headers={"Content-Type": "application/json"}
            )
            
            # Print full response details for debugging
            self.console.print(f"\n[cyan]🔍 VERBOSE: Shibboleth Response Details[/cyan]")
            self.console.print(f"[cyan]Status Code:[/cyan] {response.status_code}")
            self.console.print(f"[cyan]Response Headers:[/cyan]")
            for key, value in response.headers.items():
                self.console.print(f"  {key}: {value}")
            self.console.print(f"[cyan]Response Body:[/cyan]")
            self.console.print(response.text)
            
            if response.status_code not in [200, 201]:
                self.console.print(f"\n[red]Registration failed with status {response.status_code}[/red]")
                
                # Try to parse JSON error
                try:
                    error_data = response.json()
                    self.console.print(f"\n[red]Error:[/red] {error_data.get('error', 'Unknown')}")
                    self.console.print(f"[red]Description:[/red] {error_data.get('error_description', 'No description')}")
                except:
                    self.console.print(f"[red]Could not parse error response as JSON[/red]")
                
                raise typer.Exit(1)
            
            result = response.json()
            self.console.print(f"\n[green]✅ Registration successful![/green]")
            self.console.print(f"[green]Client ID:[/green] {result['client_id']}")
            self.console.print(f"[green]Client Secret Length:[/green] {len(result['client_secret'])} characters")
            
            return result["client_id"], result["client_secret"]
            
        except requests.exceptions.RequestException as e:
            self.console_utils.print_error(f"Failed to connect to OIDC provider: {e}", exit_code=1)