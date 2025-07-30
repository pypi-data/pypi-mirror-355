"""
Step 4: Frontend Configuration
- Update frontend config files with new client ID
- Handle both sandbox and root configs for legislative-review
"""
import re
from pathlib import Path
from utils import ConsoleUtils, AppConfig
from utils.shared_console import get_shared_console


class FrontendConfigStep:
    """Handle frontend configuration updates."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def detect_frontend_config(self, app: str, stage: str, dev_initials: str) -> tuple[str, Path]:
        """Detect frontend configuration and get URL."""
        from utils import AppConfig
        import shutil
        
        project_root = AppConfig.get_project_root()
        
        # Get all frontend paths using centralized method
        frontend_paths = AppConfig.get_all_frontend_paths()
        
        if app not in frontend_paths:
            self.console_utils.print_error(f"Unknown application: {app}", exit_code=1)
        
        frontend_dir = frontend_paths[app]
        if not frontend_dir.exists():
            self.console_utils.print_error(f"Frontend directory not found: {frontend_dir}", exit_code=1)
        
        # Find config file path
        config_dir = frontend_dir / "config" / stage
        frontend_config_path = None
        
        if config_dir.exists():
            # Look for .env.production file
            env_prod_file = config_dir / ".env.production"
            
            # If .env.production doesn't exist but .env.production.example does, create it
            if not env_prod_file.exists():
                example_file = config_dir / ".env.production.example"
                if example_file.exists():
                    self.console.print(f"  → Creating .env.production from example file")
                    shutil.copy2(example_file, env_prod_file)
                    self.console.print(f"  ✓ Created config file: [green]{env_prod_file}[/green]")
                    frontend_config_path = env_prod_file
                else:
                    # Look for other env files
                    env_files = [
                        config_dir / ".env",
                        config_dir / f".env.{stage}"
                    ]
                    
                    for env_file in env_files:
                        if env_file.exists():
                            self.console.print(f"  ✓ Found config file: [green]{env_file}[/green]")
                            frontend_config_path = env_file
                            break
            else:
                self.console.print(f"  ✓ Found config file: [green]{env_prod_file}[/green]")
                frontend_config_path = env_prod_file
        
        # Always construct URL based on app and dev initials from TOML config
        # Never read from env files as they may contain outdated URLs
        if AppConfig.is_application(app):
            # Applications use the app name directly
            frontend_url = f"https://{app}-{dev_initials}.it-eng-ai.aws.umd.edu/"
        else:
            # Components use the app name directly
            frontend_url = f"https://{app}-{dev_initials}.it-eng-ai.aws.umd.edu/"
        
        self.console.print(f"  ✓ Frontend URL from TOML config: [cyan]{frontend_url}[/cyan]")
        
        # Ensure trailing slash
        if not frontend_url.endswith("/"):
            frontend_url += "/"
            self.console.print(f"  ⚠ Added required trailing slash")
        
        return frontend_url, frontend_config_path
    
    def update_frontend_config(self, client_id: str, config_path: Path, app: str = None, frontend_dir: Path = None):
        """Update frontend configuration with new client ID."""
        def update_config_file(file_path: Path, description: str):
            """Helper to update a single config file."""
            try:
                # Read current config
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Update VITE_OIDC_CLIENT_ID
                pattern = r'VITE_OIDC_CLIENT_ID="[^"]*"'
                replacement = f'VITE_OIDC_CLIENT_ID="{client_id}"'
                
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                else:
                    # Add if not present
                    content += f'\n{replacement}\n'
                
                # Write back
                with open(file_path, 'w') as f:
                    f.write(content)
                
                self.console.print(f"    ✓ Updated {description}: {file_path}")
                
            except Exception as e:
                self.console.print(f"    ⚠ Failed to update {description}: {e}")
        
        # Update the provided config file (usually sandbox config)
        if config_path:
            update_config_file(config_path, "sandbox config")
        
        # For application apps, also update the root config file
        from utils import AppConfig
        import shutil
        if AppConfig.is_application(app) and frontend_dir:
            root_config_path = frontend_dir / ".env.production"
            
            # If root config doesn't exist, create it from the sandbox config
            if not root_config_path.exists() and config_path and config_path.exists():
                self.console.print(f"    → Creating root .env.production from sandbox config")
                shutil.copy2(config_path, root_config_path)
                self.console.print(f"    ✓ Created root config: [green]{root_config_path}[/green]")
            
            # Now update it
            if root_config_path.exists():
                update_config_file(root_config_path, "root config")
            else:
                self.console.print(f"    ⚠ Could not create root config file: {root_config_path}")