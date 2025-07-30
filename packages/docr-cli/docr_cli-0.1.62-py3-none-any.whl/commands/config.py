"""Configuration display command."""
import typer
from typing import Optional, Dict, Any
from pathlib import Path
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import shutil

from utils import AppConfig, ConsoleUtils

app = typer.Typer()


@app.command()  
def frontend(
    application: str = typer.Option(..., "--app", "-a", help="Application to configure (required)"),
    force: bool = typer.Option(False, "--force", help="Force regeneration of existing configs")
):
    """Generate frontend configuration files."""
    console_utils = ConsoleUtils()
    
    # Call refresh first  
    from commands.refresh import refresh_config
    refresh_config()
    
    # Validate provided application exists
    if not AppConfig.is_application(application):
        available_apps = AppConfig.discover_applications()
        console_utils.print_error(
            f"Unknown application: {application}\n"
            f"Available applications: {', '.join(available_apps)}",
            exit_code=1
        )
    
    # Call the moved config generation logic
    generate_frontend_config(application, force)


def generate_frontend_config(application: str, force: bool):
    """Generate frontend configuration files for the specified application."""
    console_utils = ConsoleUtils()
    
    # Get frontend directory for the application
    frontend_dir = AppConfig.get_app_frontend_dir(application)
    
    # Check if config already exists and force flag
    target_env_file = frontend_dir / ".env.production"
    if target_env_file.exists() and not force:
        console_utils.print_info(f"Configuration already exists: {target_env_file}")
        console_utils.print_info("Use --force to regenerate existing configuration.")
        return
    
    # Load TOML configuration (source of truth)
    config = AppConfig.load_config()
    # Use AppConfig to get developer initials (respects override)
    dev_initials = AppConfig.get_developer_initials()
    
    # Use passed application parameter
    active_app = application
    
    sandbox_env_file = frontend_dir / "config" / "sandbox" / ".env.production"
    
    # Check if sandbox config exists (from OIDC registration)
    use_sandbox_config = sandbox_env_file.exists()
    
    if use_sandbox_config:
        console_utils.print_info(f"Found existing sandbox config, will update and copy to root...")
    else:
        console_utils.print_info(f"Generating environment file from TOML configuration...")
    
    # Generate environment variables from TOML data
    env_vars = {}
    
    # Get API URLs from TOML configuration
    app_config = config.get('applications', {}).get(active_app, {})
    components = config.get('components', {})
    
    # Main API URL - from the active application
    if 'stage_sandbox_api_url' in app_config:
        env_vars['VITE_API_URL'] = app_config['stage_sandbox_api_url']
    
    # Component API URLs - from components configuration
    if 'costs' in components and 'stage_sandbox_api_url' in components['costs']:
        env_vars['VITE_COSTS_API_URL'] = components['costs']['stage_sandbox_api_url']
    
    if 'workspaces' in components and 'stage_sandbox_api_url' in components['workspaces']:
        # Use workspaces URL as-is (already has /api suffix)
        env_vars['VITE_WORKSPACES_API_URL'] = components['workspaces']['stage_sandbox_api_url']
    
    if 'jobs' in components and 'stage_sandbox_api_url' in components['jobs']:
        # Use jobs URL as-is
        jobs_url = components['jobs']['stage_sandbox_api_url']
        if jobs_url:  # Only set if not empty
            env_vars['VITE_JOBS_API_URL'] = jobs_url
    
    # OIDC Configuration - static values
    env_vars['VITE_OIDC_DEVMODE'] = 'false'
    env_vars['VITE_OIDC_AUTHORITY'] = 'https://shib.idm.dev.umd.edu/'
    
    # Application URL - generate based on app and developer initials
    env_vars['VITE_APP_URL'] = f"https://{active_app}-{dev_initials}.it-eng-ai.aws.umd.edu"
    
    # Debug settings
    env_vars['VITE_DEBUG_MODE'] = 'false'
    env_vars['VITE_WORKSPACES_DEBUG_LOGGING'] = 'true'
    
    # Developer configuration for scripts
    env_vars['DEV_INITIALS'] = dev_initials
    env_vars['DEFAULT_CONTACT'] = 'cmann@umd.edu'
    env_vars['APP_KEY'] = active_app
    
    # OIDC table name and scripts directory
    oidc_app_config = config.get('applications', {}).get('oidc-manager', {})
    if 'oidc_client_table_name' in oidc_app_config:
        env_vars['OIDC_RESOURCES_TABLE_NAME'] = oidc_app_config['oidc_client_table_name']
    
    # OIDC scripts directory
    project_root = config.get('project', {}).get('root', '')
    env_vars['OIDC_SCRIPTS_DIR'] = f"{project_root}/oidc-oidcauthorizer-serverless/scripts"
    
    # Extract API Gateway ID from main API URL for compatibility
    main_api_url = env_vars.get('VITE_API_URL', '')
    if 'execute-api' in main_api_url:
        # Extract ID from URL like https://4hfd40sch0.execute-api.us-east-1.amazonaws.com/
        import re
        match = re.search(r'https://([^.]+)\.execute-api', main_api_url)
        if match:
            env_vars['API_GATEWAY_ID'] = match.group(1)
    
    # Get OIDC Client ID - ALL apps should get dynamically generated client IDs
    client_id = _get_oidc_client_id_from_dynamodb(active_app, config, console_utils)
    
    if not client_id:
        # No client ID found - check if this is a self-referencing OIDC app
        if app_config.get('is_oidc_self_client', False):
            # This is a self-referencing OIDC app that needs registration
            import typer
            from rich.console import Console
            from rich.panel import Panel
            from utils.shared_console import get_shared_console
            
            console = get_shared_console()
            
            # Show warning and use placeholder
            console.print()
            console.print(Panel.fit(
                f"[bold yellow]⚠️  OIDC Self-Client Application Detected[/bold yellow]\n\n"
                f"The [cyan]{active_app}[/cyan] frontend requires OIDC client registration to function properly.\n\n"
                f"[bold]What this means:[/bold]\n"
                f"• This application authenticates users through OIDC\n"
                f"• It needs its own OIDC client ID to work\n"
                f"• The client ID comes from registering with the OIDC service\n\n"
                f"[bold]After configuration and deployment complete, you MUST:[/bold]\n"
                f"1. Run: [green]docr oidc register {active_app}[/green]\n"
                f"2. Run: [green]docr config frontend {active_app} --force[/green] (to update with real client ID)\n"
                f"3. Run: [green]docr deploy frontend --s3-only[/green] (to deploy with real client ID)\n\n"
                f"[dim]This initial configuration will use a placeholder client ID.[/dim]",
                title="OIDC Registration Required",
                border_style="yellow"
            ))
            
            if not typer.confirm("\nDo you understand these steps and want to continue?"):
                console_utils.print_error("Configuration cancelled by user", exit_code=1)
                return
            
            env_vars['VITE_OIDC_CLIENT_ID'] = '"placeholder-oidc-client-id"'
            console_utils.print_warning("Using placeholder OIDC client ID for initial configuration")
        else:
            # Regular app but no client ID found - this should not happen after OIDC registration
            console_utils.print_error(
                f"No OIDC client ID found for {active_app}!\n"
                f"Please run 'docr oidc register all' to register OIDC clients.",
                exit_code=1
            )
            return
    else:
        # Found registered client ID (works for both regular and self-client apps)
        env_vars['VITE_OIDC_CLIENT_ID'] = f'"{client_id}"'
        console_utils.print_success(f"Using registered OIDC client ID: {client_id[:8]}...")
    
    # Write or update environment file
    try:
        if use_sandbox_config:
            # Read existing sandbox config
            with open(sandbox_env_file, 'r') as f:
                existing_content = f.read()
            
            # Parse existing env vars
            existing_vars = {}
            for line in existing_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_vars[key.strip()] = value.strip()
            
            # Update with new values from TOML, preserving OIDC client ID
            if 'VITE_OIDC_CLIENT_ID' in existing_vars:
                # Preserve the OIDC client ID from sandbox
                env_vars['VITE_OIDC_CLIENT_ID'] = existing_vars['VITE_OIDC_CLIENT_ID']
            
            # Update sandbox file with merged values
            with open(sandbox_env_file, 'w') as f:
                f.write("# API Configuration (Updated from TOML)\n")
                for key in ['VITE_API_URL', 'VITE_COSTS_API_URL', 'VITE_WORKSPACES_API_URL', 'VITE_JOBS_API_URL']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                
                f.write("\n# OIDC Configuration\n")
                for key in ['VITE_OIDC_DEVMODE', 'VITE_OIDC_AUTHORITY', 'VITE_OIDC_CLIENT_ID']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                
                f.write("\n# Application Configuration\n")
                for key in ['VITE_APP_URL', 'VITE_DEBUG_MODE', 'VITE_WORKSPACES_DEBUG_LOGGING']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                
                f.write("\n# Developer Configuration\n")
                for key in ['DEV_INITIALS', 'OIDC_SCRIPTS_DIR', 'OIDC_RESOURCES_TABLE_NAME', 'DEFAULT_CONTACT', 'APP_KEY', 'API_GATEWAY_ID']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
            
            # Copy sandbox config to root
            shutil.copy2(sandbox_env_file, target_env_file)
            console_utils.print_success(f"✓ Updated sandbox config and copied to root")
        else:
            # No sandbox config exists, create both sandbox and root files
            # First create the sandbox directory if it doesn't exist
            sandbox_env_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create sandbox config file
            with open(sandbox_env_file, 'w') as f:
                f.write("# API Configuration (Generated from TOML)\n")
                for key in ['VITE_API_URL', 'VITE_COSTS_API_URL', 'VITE_WORKSPACES_API_URL', 'VITE_JOBS_API_URL']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                
                f.write("\n# OIDC Configuration\n")
                for key in ['VITE_OIDC_DEVMODE', 'VITE_OIDC_AUTHORITY', 'VITE_OIDC_CLIENT_ID']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                
                f.write("\n# Application Configuration\n")
                for key in ['VITE_APP_URL', 'VITE_DEBUG_MODE', 'VITE_WORKSPACES_DEBUG_LOGGING']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
                
                f.write("\n# Developer Configuration\n")
                for key in ['DEV_INITIALS', 'OIDC_SCRIPTS_DIR', 'OIDC_RESOURCES_TABLE_NAME', 'DEFAULT_CONTACT', 'APP_KEY', 'API_GATEWAY_ID']:
                    if key in env_vars:
                        f.write(f"{key}={env_vars[key]}\n")
            
            # Copy sandbox config to root
            shutil.copy2(sandbox_env_file, target_env_file)
            console_utils.print_success(f"✓ Created sandbox config and copied to root")
        
        console_utils.print_success(f"✓ Configuration written to: {target_env_file}")
        
        # Generate samconfig.toml for frontend deployments
        console_utils.print_info("ℹ️ Generating samconfig.toml for frontend deployment...")
        samconfig_example = frontend_dir / "samconfig.toml.example"
        samconfig_target = frontend_dir / "samconfig.toml"
        
        if samconfig_example.exists():
            try:
                # Read example content
                content = samconfig_example.read_text()
                
                # Replace developer initials (handle common placeholders)
                # Use AppConfig to get developer initials (respects override)
                dev_initials = AppConfig.get_developer_initials()
                content = content.replace("jm1", dev_initials)
                content = content.replace("cm2", dev_initials)
                content = content.replace("cm9", dev_initials)
                
                # Write samconfig.toml
                samconfig_target.write_text(content)
                console_utils.print_success(f"✓ Generated samconfig.toml with developer initials: {dev_initials}")
            except Exception as e:
                console_utils.print_warning(f"⚠️  Could not generate samconfig.toml: {e}")
        else:
            # Check alternative naming convention
            samconfig_example_alt = frontend_dir / "samconfig.example.toml"
            if samconfig_example_alt.exists():
                try:
                    # Read example content
                    content = samconfig_example_alt.read_text()
                    
                    # Replace developer initials
                    # Use AppConfig to get developer initials (respects override)
                    dev_initials = AppConfig.get_developer_initials()
                    content = content.replace("jm1", dev_initials)
                    content = content.replace("cm2", dev_initials)
                    content = content.replace("cm9", dev_initials)
                    
                    # Write samconfig.toml
                    samconfig_target.write_text(content)
                    console_utils.print_success(f"✓ Generated samconfig.toml with developer initials: {dev_initials}")
                except Exception as e:
                    console_utils.print_warning(f"⚠️  Could not generate samconfig.toml: {e}")
            else:
                console_utils.print_info("ℹ️ No samconfig.toml.example found - skipping samconfig generation")
        
    except Exception as e:
        console_utils.print_error(f"❌ Failed to generate environment file: {e}")
        return


def _get_oidc_client_id_from_dynamodb(app_name: str, config: dict, console_utils: ConsoleUtils) -> Optional[str]:
    """Get OIDC client ID from DynamoDB for self-referencing apps."""
    try:
        import boto3
        import time
        from botocore.exceptions import ClientError
        
        # Get DynamoDB table name from OIDC manager config
        oidc_manager_config = config.get('applications', {}).get('oidc-manager', {})
        table_name = oidc_manager_config.get('oidc_client_table_name')
        
        if not table_name:
            console_utils.print_error(
                "OIDC client table name not found in configuration.\n"
                "Please ensure the oidc-manager backend stack is deployed first.\n"
                "Then run 'docr refresh' to update configuration with the table name.",
                exit_code=1
            )
            return None
        
        # Get developer initials for client name pattern
        # Use AppConfig to get developer initials (respects override)
        dev_initials = AppConfig.get_developer_initials()
        expected_client_name = f"{app_name}-{dev_initials}"
        
        # Create DynamoDB client
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(table_name)
        
        # Retry logic for eventual consistency
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            if attempt > 0:
                console_utils.print_info(f"Retrying DynamoDB query (attempt {attempt + 1}/{max_retries})...")
                time.sleep(retry_delay)
            
            # Query the table using the correct key structure
            # PK = "ORG#UMD#CLIENT", then filter by client_name
            response = table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key('PK').eq('ORG#UMD#CLIENT'),
                FilterExpression=boto3.dynamodb.conditions.Attr('client_name').eq(expected_client_name)
            )
            
            if response['Items']:
                # Extract client ID from SK field: "CLIENT#{client_id}"
                item = response['Items'][0]  # Take first match
                sk = item.get('SK', '')
                if sk.startswith('CLIENT#'):
                    client_id = sk[7:]  # Remove "CLIENT#" prefix
                    return client_id
            
            # If this is not the last attempt, log what we're looking for
            if attempt < max_retries - 1:
                console_utils.print_warning(f"Client '{expected_client_name}' not found in DynamoDB yet...")
        
        return None
            
    except ClientError as e:
        console_utils.print_warning(f"Could not access DynamoDB: {e}")
        return None
    except Exception as e:
        console_utils.print_warning(f"Error retrieving client ID: {e}")
        return None


def show_config():
    """Display current configuration."""
    console_utils = ConsoleUtils()
    
    try:
        # Load and display configuration
        config_info = AppConfig.get_app_info()
        
        # Create main config table
        config_table = Table(show_header=False, box=None)
        config_table.add_column("Key", style="cyan")
        config_table.add_column("Value", style="green")
        
        config_table.add_row("Project Root", str(config_info['project_root']))
        config_table.add_row("Config File", str(config_info['config_file']))
        config_table.add_row("Developer Initials", config_info['developer_initials'])
        config_table.add_row("Last Updated", config_info['last_updated'])
        
        console_utils.console.print(Panel(config_table, title="[bold]Doc Review Configuration[/bold]"))
        
        # Show available applications
        if config_info['available_applications']:
            apps_table = Table(title="Available Applications")
            apps_table.add_column("Name", style="cyan")
            apps_table.add_column("Type", style="yellow")
            
            for app in config_info['available_applications']:
                apps_table.add_row(app, "Application")
            
            console_utils.console.print(apps_table)
        
        # Show available components
        if config_info['available_components']:
            components_table = Table(title="Available Components")
            components_table.add_column("Name", style="cyan")
            components_table.add_column("Type", style="yellow")
            
            for comp in config_info['available_components']:
                components_table.add_row(comp, "Component")
            
            console_utils.console.print(components_table)
        
        # Show hints
        console_utils.console.print("\n[dim]Hints:[/dim]")
        console_utils.console.print("[dim]• Run 'docr refresh' to update API URLs from AWS[/dim]")
        console_utils.console.print("[dim]• Run 'docr config backend --all' to generate backend configurations[/dim]")
        console_utils.console.print("[dim]• Run 'docr tools' to see all available commands[/dim]")
        
    except FileNotFoundError:
        console_utils.print_error(
            "Configuration not found!\n"
            "Run 'docr setup' to create initial configuration.",
            exit_code=1
        )
    except Exception as e:
        console_utils.print_error(f"Error loading configuration: {str(e)}", exit_code=1)