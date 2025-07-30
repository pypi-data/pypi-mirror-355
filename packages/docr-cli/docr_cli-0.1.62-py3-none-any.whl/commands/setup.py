"""Setup command for initial configuration."""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple, List
import typer
from rich import print as rprint
from rich.prompt import Prompt, Confirm
import tomli_w
import yaml

from utils import ConsoleUtils
from utils.precheck import run_precheck


def run_setup(config_file: Path) -> bool:
    """Run initial setup for the Doc Review CLI."""
    console_utils = ConsoleUtils()
    
    # Run prechecks first
    if not run_precheck("setup"):
        console_utils.print_error("Setup aborted due to missing prerequisites.")
        return False
    
    rprint("\n[bold]Welcome to Doc Review CLI Setup![/bold]")
    
    # Step 1: Find project root
    rprint(f"\n[bold]Step 1: Locating project root directory[/bold]")
    
    current_dir = Path.cwd()
    rprint(f"Current directory: [cyan]{current_dir}[/cyan]")
    
    # Search for project root
    project_path = None
    check_path = current_dir
    
    # First check if we're already in the right place
    if check_path.name == "aisolutions-docreview-cli":
        # We're in the CLI directory, go up to find the root
        check_path = check_path.parent
    
    # Look for the doc-review root directory
    while check_path != check_path.parent:
        if check_path.name == "doc-review" and is_valid_project_root(check_path):
            project_path = check_path
            break
        check_path = check_path.parent
    
    if not project_path:
        # Try to find it by looking for specific subdirectories
        for parent in current_dir.parents:
            if is_valid_project_root(parent):
                project_path = parent
                break
    
    if project_path:
        rprint(f"[green]✓ Found project root: {project_path}[/green]")
        is_valid, message = validate_project_structure(project_path)
        if not is_valid:
            rprint(f"[red]Project structure validation failed: {message}[/red]")
            return False
        rprint("[green]✓ Project structure validated[/green]")
    else:
        rprint("\n[yellow]Could not automatically detect project root.[/yellow]")
        
        while True:
            manual_path = Prompt.ask(
                "Please enter the full path to your doc-review project root",
                default=str(Path.home() / "doc-review")
            )
            
            project_path = Path(manual_path).expanduser().resolve()
            
            is_valid, message = validate_project_structure(project_path)
            if is_valid:
                rprint(f"[green]✓ Valid project root: {project_path}[/green]")
                break
            else:
                rprint(f"[red]Invalid project root: {message}[/red]")
                if not Confirm.ask("Try another path?"):
                    return False
    
    # Save the absolute path
    project_path = project_path.resolve()
    
    # Step 2: Check for existing config
    if config_file.exists():
        rprint(f"\n[yellow]Existing configuration found at: {config_file}[/yellow]")
        if not Confirm.ask("Overwrite existing configuration?"):
            return False
        # Create backup
        backup_path = config_file.with_suffix('.toml.backup')
        import shutil
        shutil.copy2(config_file, backup_path)
        rprint(f"[dim]Backup saved to: {backup_path}[/dim]")
    
    # Get UMD directory ID and validate
    rprint(f"\n[bold]Developer Configuration[/bold]")
    
    # Prompt for UMD directory ID
    while True:
        directory_id = Prompt.ask(
            "Enter your UMD directory ID (e.g., cmann, jsmith1)",
            default="cmann"
        ).lower()
        
        # Validate directory ID against workspaces.yml
        is_valid, message = validate_directory_id(project_path, directory_id)
        
        if is_valid:
            rprint(f"[green]✓ {message}[/green]")
            break
        else:
            rprint(f"[red]✗ {message}[/red]")
            rprint(f"[red]You need to be added to the workspaces configuration before you can use the application.[/red]")
            rprint(f"[yellow]Please add yourself to: {project_path}/aisolutions-docreview-serverless/legislative-review-backend/config/bootstrap/sandbox/workspaces.yml[/yellow]")
            rprint(f"[yellow]Add your directory ID to the 'admins' and/or 'members' lists in the appropriate workspace(s), similar to other developers.[/yellow]")
            
            if not Confirm.ask("Try another directory ID?"):
                rprint(f"[red]Setup aborted. Please ensure you are added to workspaces.yml before running setup again.[/red]")
                return False
    
    # Get developer initials for AWS resource naming
    dev_initials = Prompt.ask(
        "Enter your developer initials for AWS resource naming (e.g., cdm, jds)",
        default="cdm"
    ).lower()
    
    # Discover and populate TOML with static values only
    rprint(f"\n[cyan]Discovering applications and components...[/cyan]")
    toml_data = discover_and_populate_toml(project_path, dev_initials, directory_id)
    
    # Show discovered items
    discovered_apps = list(toml_data["applications"].keys())
    discovered_components = list(toml_data["components"].keys())
    
    if discovered_apps:
        rprint(f"[green]✓ Discovered applications:[/green] {', '.join(discovered_apps)}")
    if discovered_components:
        rprint(f"[green]✓ Discovered components:[/green] {', '.join(discovered_components)}")
    
    # Check that applications were found
    if len(discovered_apps) == 0:
        rprint(f"\n[red]No applications found! Make sure legislative-review-backend exists.[/red]")
        return False
    
    # Save TOML configuration
    save_config(toml_data, config_file)
    
    rprint(f"\n[green]✓ Configuration saved to {config_file}[/green]")
    rprint(f"[green]✓ Project root: {project_path}[/green]")
    
    rprint(f"\n[bold green]Setup complete! Next steps:[/bold green]")
    rprint(f"1. Run [cyan]docr install[/cyan] for automated deployment of the entire system")
    rprint(f"   [dim]OR manually:[/dim]")
    rprint(f"   • Deploy your backend stacks if not already deployed")
    rprint(f"   • Run [cyan]docr refresh[/cyan] to populate API URLs and Lambda function names")
    rprint(f"   • Run [cyan]docr oidc register[/cyan] to set up OIDC clients")
    
    return True


def is_valid_project_root(path: Path) -> bool:
    """Check if a path looks like a valid doc-review project root."""
    # Check for expected subdirectories
    expected_dirs = [
        "aisolutions-docreview-serverless",
        "aisolutions-docreview-cli"
    ]
    
    for dir_name in expected_dirs:
        if not (path / dir_name).exists():
            return False
    
    return True


def validate_directory_id(project_root: Path, directory_id: str) -> Tuple[bool, str]:
    """Validate if directory ID exists in workspaces.yml file."""
    workspaces_path = project_root / "aisolutions-docreview-serverless" / "legislative-review-backend" / "config" / "bootstrap" / "sandbox" / "workspaces.yml"
    
    if not workspaces_path.exists():
        return False, f"Could not find workspaces configuration at: {workspaces_path}"
    
    try:
        with open(workspaces_path, 'r') as f:
            workspaces_data = yaml.safe_load(f)
        
        # Collect all user IDs from all workspaces
        all_users = set()
        
        if 'organizations' in workspaces_data:
            for org in workspaces_data['organizations']:
                if 'workspaces' in org:
                    for workspace in org['workspaces']:
                        if 'admins' in workspace:
                            all_users.update(workspace['admins'])
                        if 'members' in workspace:
                            all_users.update(workspace['members'])
        
        if directory_id in all_users:
            return True, f"Found '{directory_id}' in workspaces configuration"
        else:
            return False, f"Directory ID '{directory_id}' not found in any workspace"
            
    except Exception as e:
        return False, f"Error reading workspaces.yml: {str(e)}"


def validate_project_structure(project_root: Path) -> Tuple[bool, str]:
    """Validate that the project structure is correct."""
    # Check for critical directories
    required_dirs = {
        "aisolutions-docreview-serverless/legislative-review-backend": "Main application backend",
        "aisolutions-docreview-serverless/legislative-review-frontend": "Main application frontend",
    }
    
    for dir_path, description in required_dirs.items():
        full_path = project_root / dir_path
        if not full_path.exists():
            return False, f"Missing {description}: {dir_path}"
    
    return True, "All required directories found"


def discover_and_populate_toml(project_root: Path, dev_initials: str, directory_id: str) -> Dict[str, Any]:
    """Discover applications and components and create TOML structure."""
    import datetime
    
    toml_data = {
        "project": {
            "name": "doc-review",
            "root": str(project_root),
            "setup_completed": True,
            "last_updated": datetime.datetime.now().isoformat(),
            "developer_initials": dev_initials,
            "directory_id": directory_id
        },
        "applications": {},
        "components": {},
        "oidc": {
            "authorizer": {
                "directory_name": "oidc-oidcauthorizer-serverless",
                "stack_name": f"oidc-lambda-authorizer-shared-{dev_initials}"
            },
            "manager": {
                "directory_name": "oidc-oidcmanager-serverless/oidc-manager-backend"
            },
            "directories": {
                "oidc-authorizer": "oidc-oidcauthorizer-serverless",
                "oidc-manager": "oidc-oidcmanager-serverless/oidc-manager-backend"
            }
        },
        "credstore": {
            "table_name": "UmdMockCredStore"
        },
        "expected_modules": {
            "modules": []
        },
        "deployment": {
            "ecr_registry": "495686535940.dkr.ecr.us-east-1.amazonaws.com"
        }
    }
    
    # Discover applications
    apps_config = {
        "legislative-review": {
            "directory_name": "docreview",
            "backend_path": "aisolutions-docreview-serverless/legislative-review-backend",
            "frontend_path": "aisolutions-docreview-serverless/legislative-review-frontend",
            "stack_name": f"legislative-review-{dev_initials}",
            "api_name": "LegislativeReviewApi",
            "credstore_product": f"legislative-review-{dev_initials}",
            "is_oidc_self_client": False,
            "verify_all_clients": True
        },
        "oidc-manager": {
            "directory_name": "oidc-manager",
            "backend_path": "oidc-oidcmanager-serverless/oidc-manager-backend",
            "frontend_path": "oidc-oidcmanager-serverless/oidc-manager-frontend",
            "stack_name": f"oidc-app-{dev_initials}",
            "api_name": "OidcManagerApi",
            "credstore_product": f"oidc-app-{dev_initials}",
            "is_oidc_self_client": True,
            "verify_all_clients": False
        }
    }
    
    # Add discovered applications with static config
    for app_name, app_config in apps_config.items():
        backend_path = project_root / app_config["backend_path"]
        frontend_path = project_root / app_config["frontend_path"]
        
        if backend_path.exists():
            toml_data["applications"][app_name] = {
                "directory_name": app_config["directory_name"],
                "backend_path": app_config["backend_path"],
                "frontend_path": app_config["frontend_path"],
                "stack_name": app_config["stack_name"],
                "api_name": app_config["api_name"],
                "credstore_product": app_config["credstore_product"],
                "secret_key": f"{app_name}-secret-{dev_initials}",
                "is_oidc_self_client": app_config.get("is_oidc_self_client", False),
                "verify_all_clients": app_config.get("verify_all_clients", False),
                # API URLs from frontend environment configurations
                "stage_sandbox_api_url": "https://sx3xhwws58.execute-api.us-east-1.amazonaws.com/",
                "stage_dev_api_url": "https://uxunw3dgv1.execute-api.us-east-1.amazonaws.com/",
                "stage_qa_api_url": "https://5cg8eo614m.execute-api.us-east-1.amazonaws.com/api/",
                "stage_prod_api_url": "https://cyeftr01ui.execute-api.us-east-1.amazonaws.com/api/",
                "lambda_function_name": "",  # Populated by refresh
                "stage_sandbox_frontend_url": "",  # Populated by refresh
                "sns_topic_arn": "",  # Populated by refresh - needed for jobs
                # Special case for oidc-manager which doesn't use -frontend suffix
                "frontend_stack_name": f"{app_name}-{dev_initials}" if app_name == "oidc-manager" else f"{app_name}-frontend-{dev_initials}"
            }
    
    # Discover components
    components_config = {
        "costs": {
            "directory_name": "costsmodule",
            "backend_path": "aisolutions-costsmodule-serverless/cost-component-backend",
            "frontend_path": "aisolutions-costsmodule-serverless/cost-component-frontend",
            "stack_name": f"costs-app-{dev_initials}",
            "api_name": "CostComponentApi",
            "credstore_product": f"costs-app-{dev_initials}",
            "bootstrap_supported": False,
            "npm_package": "@ai-sandbox/cost-component-react",
            "npm_alias": "cost-component",
            "client_name": "cost",
            # API URLs from frontend environment configurations
            "stage_sandbox_api_url": "https://gupk5vylw8.execute-api.us-east-1.amazonaws.com/api",
            "stage_dev_api_url": "https://mtc3j8sjng.execute-api.us-east-1.amazonaws.com/api",
            "stage_qa_api_url": "https://gupk5vylw8.execute-api.us-east-1.amazonaws.com/api",
            "stage_prod_api_url": ""
        },
        "jobs": {
            "directory_name": "jobsmodule",
            "backend_path": "aisolutions-jobsmodule-serverless/jobs-component-backend",
            "frontend_path": "aisolutions-jobsmodule-serverless/jobs-component-frontend",
            "stack_name": f"jobs-app-{dev_initials}",
            "api_name": "JobsComponentApi",
            "credstore_product": f"jobs-app-{dev_initials}",
            "bootstrap_supported": False,
            "npm_package": "@ai-sandbox/jobs-component-react",
            "npm_alias": "jobs-component",
            "client_name": "job",
            # API URLs from frontend environment configurations
            "stage_sandbox_api_url": "",  # Jobs component not deployed to sandbox yet
            "stage_dev_api_url": "",  # Jobs component not deployed to dev yet
            "stage_qa_api_url": "https://i65ge6mc75.execute-api.us-east-1.amazonaws.com/api",
            "stage_prod_api_url": ""
        },
        "workspaces": {
            "directory_name": "workspaces",
            "backend_path": "aisolutions-workspaces-serverless/workspaces-component-backend",
            "frontend_path": "aisolutions-workspaces-serverless/workspaces-component-frontend",
            "stack_name": f"workspaces-app-{dev_initials}",
            "api_name": "WorkspacesComponentApi",
            "credstore_product": f"workspaces-app-{dev_initials}",
            "bootstrap_supported": True,
            "npm_package": "@ai-sandbox/workspaces-component-react",
            "npm_alias": "workspaces-component",
            "client_name": "workspace",
            # API URLs from frontend environment configurations
            "stage_sandbox_api_url": "https://yz9e53kbxb.execute-api.us-east-1.amazonaws.com/api",
            "stage_dev_api_url": "https://pf0kiqnp7h.execute-api.us-east-1.amazonaws.com/api",
            "stage_qa_api_url": "https://yz9e53kbxb.execute-api.us-east-1.amazonaws.com/api",
            "stage_prod_api_url": ""
        }
    }
    
    # Add discovered components
    for component_name, component_config in components_config.items():
        backend_path = project_root / component_config["backend_path"]
        frontend_path = project_root / component_config["frontend_path"]
        
        if backend_path.exists():
            component_data = {
                "directory_name": component_config["directory_name"],
                "backend_path": component_config["backend_path"],
                "frontend_path": component_config["frontend_path"],
                "stack_name": component_config["stack_name"],
                "api_name": component_config["api_name"],
                "credstore_product": component_config["credstore_product"],
                "secret_key": f"{component_config['client_name']}-secret-{dev_initials}",
                "bootstrap_supported": component_config["bootstrap_supported"],
                "npm_package": component_config["npm_package"],
                "npm_alias": component_config["npm_alias"],
                "client_name": component_config["client_name"],
                # API URLs from frontend environment configurations
                "stage_sandbox_api_url": component_config.get("stage_sandbox_api_url", ""),
                "stage_dev_api_url": component_config.get("stage_dev_api_url", ""),
                "stage_qa_api_url": component_config.get("stage_qa_api_url", ""),
                "stage_prod_api_url": component_config.get("stage_prod_api_url", ""),
                "lambda_function_name": "",  # Populated by refresh
                "sns_topic_arn": ""  # Jobs component may have this
            }
            
            # Don't fetch stack outputs during setup - that's for refresh
            toml_data["components"][component_name] = component_data
    
    # Build expected modules list
    toml_data["expected_modules"]["modules"] = [
        item.name for item in project_root.iterdir() 
        if item.is_dir() and (
            item.name.startswith('aisolutions-') or 
            item.name.startswith('oidc-')
        )
    ]
    
    return toml_data


def save_config(config_data: Dict[str, Any], config_file: Path):
    """Save configuration to TOML file."""
    # Ensure directory exists
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write TOML file
    with open(config_file, 'wb') as f:
        tomli_w.dump(config_data, f)


def check_or_setup_config(config_file: Path) -> bool:
    """Check if config exists, if not run setup"""
    try:
        import tomllib
        config = {}
        if config_file.exists():
            with open(config_file, 'rb') as f:
                config = tomllib.load(f)
        
        if not config or 'project' not in config or 'root' not in config['project']:
            rprint("\n[yellow]First time setup required![/yellow]")
            return run_setup(config_file)
        
        # Validate existing config
        project_root = Path(config['project']['root'])
        if not project_root.exists():
            rprint(f"\n[red]Configured project root no longer exists: {project_root}[/red]")
            return run_setup(config_file)
        
        is_valid, message = validate_project_structure(project_root)
        if not is_valid:
            rprint(f"\n[red]Project structure validation failed: {message}[/red]")
            if Confirm.ask("Run setup again?"):
                return run_setup(config_file)
            return False
        
        return True
    except Exception as e:
        rprint(f"\n[red]Error loading configuration: {e}[/red]")
        return run_setup(config_file)