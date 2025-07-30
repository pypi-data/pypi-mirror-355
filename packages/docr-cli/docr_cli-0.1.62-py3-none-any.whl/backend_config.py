#!/usr/bin/env python3
"""
Backend configuration management for Doc Review CLI.
Automates samconfig.toml and environment config generation across all components.
"""
import typer
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import tomllib
import tomli_w
import shutil
import re
from rich.table import Table
from rich.prompt import Confirm
from utils import ConsoleUtils, get_shared_console

# Use shared console for all output
console = get_shared_console()

# Create app for backend config commands
app = typer.Typer(
    name="backend",
    help="Backend configuration management",
    context_settings={"help_option_names": ["-h", "--help"]},
    rich_markup_mode="rich"
)

console_utils = ConsoleUtils()

# Component registry with all configuration details
COMPONENT_REGISTRY = {
    "costs-component": {
        "type": "component",
        "path": "aisolutions-costsmodule-serverless/cost-component-backend",
        "stack_prefix": "costs-app",
        "appkey": "costs-app",
        "outputs_expected": ["FastApiFunctionUrl"],
        "config_format": "none",  # Components don't need config files
        "config_files": [],
        "env_vars_needed": [],
        "description": "Cost tracking component"
    },
    "jobs-component": {
        "type": "component",
        "path": "aisolutions-jobsmodule-serverless/jobs-component-backend",
        "stack_prefix": "jobs-app",
        "appkey": "jobs-app",
        "outputs_expected": ["FastApiFunctionUrl", "JobTopicArn"],
        "config_format": "none",  # Components don't need config files
        "config_files": [],
        "env_vars_needed": [],
        "description": "Job processing component"
    },
    "workspaces-component": {
        "type": "component",
        "path": "aisolutions-workspaces-serverless/workspaces-component-backend",
        "stack_prefix": "workspaces-app",
        "appkey": "workspaces-app",
        "outputs_expected": ["FastApiFunctionUrl"],
        "config_format": "none",  # Components don't need config files
        "config_files": [],
        "env_vars_needed": [],
        "description": "Workspace management component"
    },
    "oidc-authorizer": {
        "type": "infrastructure",
        "path": "oidc-oidcauthorizer-serverless",
        "stack_prefix": "OidcAuthorizer",
        "appkey": "OidcAuthorizer",
        "outputs_expected": ["OidcAuthorizerUrl", "OidcAuthorizerArn"],
        "config_format": "none",  # No config files needed
        "config_files": [],
        "special_config": {
            "capabilities": "CAPABILITY_IAM CAPABILITY_NAMED_IAM",
            "initials_parameter": "DeveloperInitials",  # PascalCase, not lowercase
            "post_deploy_message": "Run 'docr oidc register all' after deployment"
        },
        "description": "Central OIDC authentication service"
    },
    "oidc-manager": {
        "type": "application",
        "path": "oidc-oidcmanager-serverless/oidc-manager-backend",
        "stack_prefix": "oidc-app",
        "appkey": "oidc-app",
        "outputs_expected": ["OidcClientTableName", "FastApiFunctionUrl"],
        "config_format": "env",
        "config_files": ["config/config.sandbox"],
        "env_vars_needed": ["UMD_AH_OIDC_CLIENT_TABLE"],
        "env_var_mappings": {
            "UMD_AH_OIDC_CLIENT_TABLE": "oidc_client_table_name"
        },
        "requires": ["oidc-authorizer"],
        "description": "OIDC management application"
    },
    "legislative-review": {
        "type": "application",
        "path": "aisolutions-docreview-serverless/legislative-review-backend",
        "stack_prefix": "legislative-review",
        "appkey": "legislative-review",
        "outputs_expected": ["FastApiFunctionUrl", "DocumentBucketName", "FastSyncLambdaName"],
        "config_format": "env",
        "config_files": ["config/config.sandbox"],
        "env_vars_needed": ["COST_API_URL", "WORKSPACES_API_URL", "JOB_API_URL"],
        "env_var_mappings": {
            "COST_API_URL": "costs_api_url",
            "WORKSPACES_API_URL": "workspaces_api_url", 
            "JOB_API_URL": "jobs_api_url"
        },
        "requires": ["costs-component", "jobs-component", "workspaces-component", "oidc-authorizer"],
        "description": "Main legislative review application"
    }
}

def load_config() -> Optional[Dict[str, Any]]:
    """Load configuration from ~/docr.toml"""
    config_file = Path.home() / "docr.toml"
    if config_file.exists():
        try:
            with open(config_file, 'rb') as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError:
            return None
    return None

def save_config(config_data: Dict[str, Any]):
    """Save configuration to ~/docr.toml"""
    config_file = Path.home() / "docr.toml"
    with open(config_file, 'wb') as f:
        tomli_w.dump(config_data, f)

def initialize_backend_registry(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """Initialize backend registry in TOML if not present"""
    if "backend_registry" not in config_data:
        config_data["backend_registry"] = COMPONENT_REGISTRY
        console_utils.print_info("Initialized backend component registry")
    return config_data

def get_component_path(project_root: Path, component: str) -> Path:
    """Get the full path to a component"""
    registry = COMPONENT_REGISTRY.get(component, {})
    return project_root / registry.get("path", "")

def check_samconfig_example(component_path: Path) -> Path:
    """Check if samconfig example file exists and contains jm1 placeholder.
    Supports both .example.toml and .toml.example naming conventions.
    Returns the path to the example file if found, None otherwise."""
    
    # Check both naming conventions
    example_files = [
        component_path / "samconfig.example.toml",
        component_path / "samconfig.toml.example"
    ]
    
    for example_file in example_files:
        if example_file.exists():
            content = example_file.read_text()
            if "jm1" not in content:
                console_utils.print_error(f"{example_file.name} doesn't contain 'jm1' placeholder")
                return None
            return example_file
    
    return None

def generate_samconfig(component_path: Path, component_info: Dict[str, Any], developer_initials: str, example_file: Path) -> bool:
    """Generate samconfig.toml from example file"""
    target_file = component_path / "samconfig.toml"
    
    if not example_file or not example_file.exists():
        console_utils.print_error(f"samconfig example file not found in {component_path}")
        return False
    
    # Read example content
    content = example_file.read_text()
    
    # Replace jm1 with developer initials
    content = content.replace("jm1", developer_initials)
    
    # Handle special cases
    if "special_config" in component_info:
        special = component_info["special_config"]
        # For OIDC authorizer, use PascalCase initials
        if special.get("initials_parameter") == "DeveloperInitials":
            # Replace DeveloperInitialsLowercase with DeveloperInitials
            content = re.sub(
                r'DeveloperInitialsLowercase="\w+"',
                f'DeveloperInitials="{developer_initials}"',
                content
            )
    
    # No backup needed - samconfig.toml files are generated and should be in .gitignore
    
    # Write new file
    target_file.write_text(content)
    console_utils.print_success(f"Generated samconfig.toml for {component_info['stack_prefix']}-{developer_initials}")
    
    return True

def get_component_api_urls(config_data: Dict[str, Any], component: str) -> Dict[str, str]:
    """Get API URLs for a component from TOML config"""
    urls = {}
    
    # Map component names to their keys in TOML components section
    component_name_mappings = {
        "costs-component": "costs",
        "jobs-component": "jobs",
        "workspaces-component": "workspaces"
    }
    
    # Map component names to their API URL keys needed for env config
    component_url_mappings = {
        "costs-component": "costs_api_url",
        "jobs-component": "jobs_api_url",
        "workspaces-component": "workspaces_api_url"
    }
    
    # Check if component has been deployed (has API URL in TOML)
    if component in component_name_mappings:
        toml_key = component_name_mappings[component]
        url_key = component_url_mappings[component]
        # Look in components section of TOML
        comp_data = config_data.get("components", {}).get(toml_key, {})
        # Check for stage_sandbox_api_url which indicates deployment
        if comp_data.get("stage_sandbox_api_url"):
            urls[url_key] = comp_data["stage_sandbox_api_url"]
    
    return urls

def check_dependencies(config_data: Dict[str, Any], component: str) -> List[str]:
    """Check if required dependencies are deployed"""
    component_info = COMPONENT_REGISTRY.get(component, {})
    requires = component_info.get("requires", [])
    
    missing = []
    for dep in requires:
        # Check if dependency has been deployed by looking for its outputs in TOML
        if dep == "oidc-authorizer":
            # Special case: check for OIDC authorizer
            # It's deployed if we have the authorizer ARN in the config
            oidc_config = config_data.get("oidc", {})
            authorizer_config = oidc_config.get("authorizer", {})
            # Check if we have the authorizer ARN (Lambda functions don't have URLs)
            if not authorizer_config.get("authorizer_arn"):
                missing.append(dep)
        else:
            # Check if component has API URL (indicating it's deployed)
            urls = get_component_api_urls(config_data, dep)
            if not urls:
                missing.append(dep)
    
    return missing

def generate_env_config(component_path: Path, component_info: Dict[str, Any], 
                       config_data: Dict[str, Any], developer_initials: str) -> bool:
    """Generate environment config files"""
    if component_info.get("config_format") == "none":
        return True  # No config files needed (e.g., OIDC authorizer)
    
    for config_file_path in component_info.get("config_files", []):
        example_file = component_path / f"{config_file_path}.example"
        target_file = component_path / config_file_path
        
        if not example_file.exists():
            console_utils.print_warning(f"Config example not found: {example_file}")
            continue
        
        # Ensure directory exists
        target_file.parent.mkdir(parents=True, exist_ok=True)
        
        # If target file doesn't exist, copy from example first
        if not target_file.exists():
            shutil.copy2(example_file, target_file)
            console_utils.print_info(f"Created {config_file_path} from example file")
        
        # Read content from target file
        content = target_file.read_text()
        
        # Replace environment variables with actual values
        if "env_var_mappings" in component_info:
            replaced_any = False
            for env_var, toml_key in component_info["env_var_mappings"].items():
                # Get value from appropriate place in TOML
                value = ""
                
                # For API URLs, get from component data
                if toml_key.endswith("_api_url"):
                    component_name = toml_key.replace("_api_url", "")
                    comp_data = config_data.get("components", {}).get(component_name, {})
                    value = comp_data.get("stage_sandbox_api_url", "")
                
                # For OIDC client table
                elif toml_key == "oidc_client_table_name":
                    # Get from OIDC manager outputs
                    oidc_data = config_data.get("applications", {}).get("oidc-manager", {})
                    value = oidc_data.get("oidc_client_table_name", "")
                
                # Replace in content
                if value:
                    content = re.sub(f"{env_var}=.*", f"{env_var}={value}", content)
                    replaced_any = True
            
            # Only write back if we replaced something
            if replaced_any:
                target_file.write_text(content)
                console_utils.print_success(f"Updated {config_file_path} with API URLs")
        else:
            console_utils.print_success(f"Generated {config_file_path}")
    
    return True

def update_backend_status(config_data: Dict[str, Any], component: str, status: Dict[str, Any]):
    """Update backend configuration status in TOML"""
    if "backend_status" not in config_data:
        config_data["backend_status"] = {}
    
    config_data["backend_status"][component] = {
        **status,
        "last_configured": datetime.now().isoformat()
    }

@app.command()
def backend(
    component: Optional[str] = typer.Argument(None, help="Component to configure"),
    all: bool = typer.Option(False, "--all", help="Configure all components"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed"),
    force: bool = typer.Option(False, "--force", help="Overwrite existing configurations"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Configure backend components for deployment"""
    
    # Set developer initials override if provided
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    # Load configuration
    config_data = load_config()
    if not config_data:
        console_utils.print_error("No configuration found. Run 'docr setup' first.")
        raise typer.Exit(1)
    
    # Initialize backend registry if needed
    config_data = initialize_backend_registry(config_data)
    
    project_root = Path(config_data["project"]["root"])
    # Use AppConfig to get developer initials (respects override)
    from utils import AppConfig
    developer_initials = AppConfig.get_developer_initials()
    
    # Determine which components to configure
    if all:
        components = list(COMPONENT_REGISTRY.keys())
    elif component:
        if component not in COMPONENT_REGISTRY:
            console_utils.print_error(f"Unknown component: {component}")
            console_utils.print_info(f"Available components: {', '.join(COMPONENT_REGISTRY.keys())}")
            raise typer.Exit(1)
        components = [component]
    else:
        # Show available components
        table = Table(title="Available Backend Components")
        table.add_column("Component", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Description")
        table.add_column("Status", style="yellow")
        
        for comp_name, comp_info in COMPONENT_REGISTRY.items():
            status = config_data.get("backend_status", {}).get(comp_name, {})
            status_text = "Configured" if status.get("samconfig_generated") else "Not configured"
            table.add_row(
                comp_name,
                comp_info["type"],
                comp_info["description"],
                status_text
            )
        
        console.print(table)
        console.print("\n[yellow]Usage:[/yellow] docr config backend <component-name> or --all")
        return
    
    # Group components by type for ordered configuration
    component_groups = {
        "component": [],
        "infrastructure": [],
        "application": []
    }
    
    for comp in components:
        comp_type = COMPONENT_REGISTRY[comp]["type"]
        component_groups[comp_type].append(comp)
    
    # Configure in dependency order
    console.print(f"\n[bold]Configuring {len(components)} backend component(s)...[/bold]")
    
    for group_name, group_components in component_groups.items():
        if not group_components:
            continue
        
        console.print(f"\n[cyan]{'='*50}[/cyan]")
        console.print(f"[bold]{group_name.title()}s[/bold]")
        console.print(f"[cyan]{'='*50}[/cyan]")
        
        for comp in group_components:
            console.print(f"\n[bold]Configuring: {comp}[/bold]")
            comp_info = COMPONENT_REGISTRY[comp]
            comp_path = get_component_path(project_root, comp)
            
            if not comp_path.exists():
                console_utils.print_error(f"Component path not found: {comp_path}")
                continue
            
            # Check dependencies (will only warn, not block)
            missing_deps = check_dependencies(config_data, comp)
            if missing_deps:
                console_utils.print_warning(f"Missing dependencies: {', '.join(missing_deps)}")
                console_utils.print_info("Deploy these components first, then run 'docr refresh'")
            
            status = {}
            
            # Phase 1: Generate samconfig.toml (always generate regardless of dependencies)
            console_utils.print_info("Generating samconfig.toml...")
            if dry_run:
                console_utils.print_info(f"Would generate samconfig.toml in {comp_path}")
                status["samconfig_generated"] = True
            else:
                example_file = check_samconfig_example(comp_path)
                if example_file:
                    if generate_samconfig(comp_path, comp_info, developer_initials, example_file):
                        status["samconfig_generated"] = True
                        console_utils.print_success(f"✓ Stack name: {comp_info['stack_prefix']}-{developer_initials}")
                    else:
                        status["samconfig_generated"] = False
                else:
                    console_utils.print_error("Missing or invalid samconfig example file")
                    status["samconfig_generated"] = False
            
            # Phase 2: Generate environment configs (only if dependencies are met or force is used)
            if comp_info.get("config_files"):
                if missing_deps and not force:
                    console_utils.print_warning("Skipping environment config generation due to missing dependencies")
                    console_utils.print_info("Use --force to generate anyway")
                else:
                    console_utils.print_info("Generating environment configs...")
                    if dry_run:
                        for cf in comp_info["config_files"]:
                            console_utils.print_info(f"Would generate {cf}")
                        status["env_config_generated"] = True
                    else:
                        if generate_env_config(comp_path, comp_info, config_data, developer_initials):
                            status["env_config_generated"] = True
                        else:
                            status["env_config_generated"] = False
            
            # Update status in TOML
            if not dry_run:
                update_backend_status(config_data, comp, status)
            
            # Show next steps
            console.print(f"\n[green]✓ {comp} configuration complete![/green]")
            
            if comp_info.get("config_format") == "none":
                console_utils.print_info("No environment config needed for this component")
            
            if "special_config" in comp_info:
                special = comp_info["special_config"]
                if "post_deploy_message" in special:
                    console_utils.print_info(f"After deployment: {special['post_deploy_message']}")
            
            console.print(f"\n[yellow]Next:[/yellow] cd {comp_path}")
            console.print("[yellow]Then:[/yellow] sam build && sam deploy")
            
            if missing_deps:
                console.print("\n[red]Warning:[/red] Deploy missing dependencies first!")
    
    # Save updated configuration
    if not dry_run:
        save_config(config_data)
        console.print("\n[green]✓ Configuration saved to ~/docr.toml[/green]")
    
    # Show summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"- Configured: {len(components)} component(s)")
    console.print(f"- Developer initials: {developer_initials}")
    
    if all:
        console.print("\n[yellow]Deploy order:[/yellow]")
        console.print("1. Components: costs, jobs, workspaces")
        console.print("2. Infrastructure: oidc-authorizer")
        console.print("3. Applications: oidc-manager, legislative-review")
        console.print("\nAfter each deployment, run 'docr refresh' to update configuration")

@app.command()
def status(
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Show backend configuration status"""
    if developer_initials:
        from utils import AppConfig
        AppConfig.set_developer_initials_override(developer_initials)
    
    config_data = load_config()
    if not config_data:
        console_utils.print_error("No configuration found. Run 'docr setup' first.")
        raise typer.Exit(1)
    
    backend_status = config_data.get("backend_status", {})
    
    table = Table(title="Backend Configuration Status")
    table.add_column("Component", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Configured", style="yellow")
    table.add_column("Deployed", style="magenta")
    table.add_column("Last Updated")
    
    for comp_name, comp_info in COMPONENT_REGISTRY.items():
        status = backend_status.get(comp_name, {})
        configured = "✓" if status.get("samconfig_generated") else "✗"
        
        # Check if deployed by looking for outputs in TOML
        deployed = "?"
        if comp_name in ["costs-component", "jobs-component", "workspaces-component"]:
            urls = get_component_api_urls(config_data, comp_name)
            deployed = "✓" if urls else "✗"
        elif comp_name == "oidc-authorizer":
            deployed = "✓" if config_data.get("oidc", {}).get("authorizer", {}).get("authorizer_arn") else "✗"
        
        last_updated = status.get("last_configured", "Never")
        if last_updated != "Never":
            # Format date nicely
            try:
                dt = datetime.fromisoformat(last_updated)
                last_updated = dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
        table.add_row(
            comp_name,
            comp_info["type"],
            configured,
            deployed,
            last_updated
        )
    
    console.print(table)

def run_backend_config(component: Optional[str] = None, all_components: bool = False, force: bool = False, developer_initials: Optional[str] = None):
    """Wrapper function to be called from main.py"""
    # Call the backend command directly with dry_run=False
    backend(component=component, all=all_components, force=force, dry_run=False, developer_initials=developer_initials)

if __name__ == "__main__":
    app()