"""
Step 1: Prerequisites Check
- Verify AWS credentials and Docker
- Discover and validate API Gateway deployments
- Ensure OIDC scripts have npm dependencies installed
"""
from typing import Dict
from pathlib import Path
from utils import AWSUtils, SystemUtils, ConsoleUtils, APIGatewayUtils, CommandUtils, OIDCConfigManager
from utils.shared_console import get_shared_console


class PrerequisitesStep:
    """Handle prerequisites checking for OIDC registration."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def check_system_prerequisites(self, require_docker: bool = False, require_aws: bool = True) -> bool:
        """Check system prerequisites (AWS, Docker, npm dependencies)."""
        self.console.print("Checking Prerequisites...")
        
        if require_aws:
            aws_valid, aws_msg = AWSUtils.verify_aws_token()
            print(aws_msg)
            if not aws_valid:
                return False
        
        if require_docker:
            docker_valid, docker_msg = SystemUtils.verify_docker()
            print(docker_msg)
            if not docker_valid:
                return False
        
        # Check and install npm dependencies for OIDC scripts
        try:
            oidc_scripts_dir = OIDCConfigManager.get_oidc_scripts_dir()
            oidc_project_dir = oidc_scripts_dir.parent
            package_json = oidc_project_dir / "package.json"
            node_modules = oidc_project_dir / "node_modules"
            
            # First check if we can run add-client.js without errors
            test_cmd = ["node", str(oidc_scripts_dir / "add-client.js"), "--help"]
            test_success, test_output = CommandUtils.run_command(
                test_cmd,
                shell=False,
                check=False,
                capture_output=True,
                cwd=str(oidc_project_dir)
            )
            
            # If the test fails (likely missing modules), install dependencies
            if not test_success and "Cannot find module" in test_output:
                self.console.print("[yellow]Installing npm dependencies for OIDC scripts...[/yellow]")
                npm_cmd = ["npm", "install"]
                npm_success, npm_output = CommandUtils.run_command(
                    npm_cmd,
                    shell=False,
                    check=False,
                    capture_output=True,
                    cwd=str(oidc_project_dir)
                )
                if npm_success:
                    self.console_utils.print_success("✅ npm dependencies installed successfully")
                else:
                    self.console_utils.print_error(
                        f"❌ Failed to install npm dependencies!\n"
                        f"Error: {npm_output}\n\n"
                        f"Please manually run:\n"
                        f"  cd {oidc_project_dir}\n"
                        f"  npm install",
                        exit_code=1
                    )
            elif not test_success:
                # Some other error with the script
                self.console_utils.print_error(
                    f"❌ OIDC scripts are not working properly!\n"
                    f"Error: {test_output}",
                    exit_code=1
                )
            # If test succeeds, dependencies are already installed
        except Exception as e:
            self.console_utils.print_error(f"❌ Could not verify OIDC scripts: {e}", exit_code=1)
        
        self.console_utils.print_success("Prerequisites check passed")
        return True
    
    def verify_api_deployments(self, stage: str) -> Dict[str, str]:
        """Verify that required API Gateways are deployed before OIDC registration."""
        self.console.print(f"\n[bold cyan]📡 Checking API Gateway Deployments[/bold cyan]")
        
        # Discover what APIs are actually deployed
        # Get API Gateway IDs from TOML configuration instead of discovery
        discovered_apis = APIGatewayUtils.get_all_api_gateway_ids(stage)
        
        if not discovered_apis:
            self.console_utils.print_error(
                "❌ No API Gateways found!\n\n"
                "OIDC registration requires deployed backend APIs to register clients with.\n"
                "Please deploy at least the legislative-review backend before running OIDC registration:\n\n"
                "  docr deploy backend legislative-review\n\n"
                "Deploy backends using: docr deploy backend <module-name>",
                exit_code=1
            )
        
        # Show what was found
        self.console.print(f"  ✓ Found {len(discovered_apis)} deployed API Gateway(s):")
        for app_name, api_id in discovered_apis.items():
            self.console.print(f"    • {app_name}: [green]{api_id}[/green]")
        
        # Check if we have the main legislative-review API
        if "legislative-review" not in discovered_apis:
            self.console_utils.print_warning(
                "⚠️  Legislative-review API not found!\n"
                "This is the main application API. OIDC clients will be registered with\n"
                "available component APIs, but the main app may not work properly.\n"
                "Consider deploying: docr deploy backend legislative-review"
            )
        
        self.console_utils.print_success(f"API Gateway verification completed - proceeding with {len(discovered_apis)} API(s)")
        return discovered_apis