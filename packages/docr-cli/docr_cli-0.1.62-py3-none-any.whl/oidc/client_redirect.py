"""
Client Redirect Registration
- Register client with redirect URIs in DynamoDB
- Handle client configuration storage
"""
import os
from rich.console import Console
from utils import ConsoleUtils, CommandUtils, OIDCConfigManager
from utils.shared_console import get_shared_console


class ClientRedirectStep:
    """Handle client redirect URI registration."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def register_client_redirect(self, client_id: str, redirect_uri: str, app: str, stage: str, dev_initials: str):
        """Register client with its redirect URI in DynamoDB."""
        # Get OIDC scripts directory using consolidated utility
        try:
            oidc_scripts_dir = OIDCConfigManager.get_oidc_scripts_dir()
        except RuntimeError as e:
            self.console.print(f"  ⚠ {e}")
            return
        
        try:
            resource_table_name = OIDCConfigManager.get_oidc_table_name(dev_initials)
            aws_region = "us-east-1"
            
            # Get secret key from config
            from utils import AppConfig
            config = AppConfig.load_config()
            
            # Check if it's an application or component
            if app in config.get('applications', {}):
                secret_key_name = config['applications'][app].get('secret_key')
            elif app in config.get('components', {}):
                secret_key_name = config['components'][app].get('secret_key')
            else:
                secret_key_name = None
                
            if not secret_key_name:
                raise ValueError(f"No secret_key defined in config for {app}")
                
            client_name = f"{app}-{dev_initials}"
            
            add_client_script = oidc_scripts_dir / "add-client.js"
            
            self.console.print(f"  → Registering client '{client_id}' with redirect URI in DynamoDB")
            
            cmd = [
                "node", str(add_client_script),
                "--client", client_id,
                "--redirect", redirect_uri,
                "--name", client_name,
                "--table", resource_table_name,
                "--secretKey", secret_key_name
            ]
            
            env = os.environ.copy()
            env["AWS_REGION"] = aws_region
            
            # Run the command directly to capture both stdout and stderr
            import subprocess
            result = subprocess.run(
                cmd,
                shell=False,
                capture_output=True,
                text=True,
                cwd=str(oidc_scripts_dir),
                env=env
            )
            
            # Check for any error indicators in either stdout or stderr
            combined_output = f"{result.stdout}\n{result.stderr}".strip()
            
            # Node.js errors often go to stderr even with exit code 0
            if result.returncode != 0 or "Error:" in combined_output or "Cannot find module" in combined_output:
                # This is a critical failure - show full error and raise exception
                self.console.print(f"[red]    ❌ Client registration FAILED![/red]")
                self.console.print(f"[red]    Exit code: {result.returncode}[/red]")
                if result.stdout:
                    self.console.print(f"[red]    Stdout: {result.stdout}[/red]")
                if result.stderr:
                    self.console.print(f"[red]    Stderr: {result.stderr}[/red]")
                raise RuntimeError(f"Failed to register client in DynamoDB: {combined_output}")
            else:
                self.console.print("    ✓ Client and redirect URI registered successfully")
                
        except Exception as e:
            self.console.print(f"[red]  ❌ Client redirect registration failed: {e}[/red]")
            raise  # Re-raise to fail the entire registration