#!/usr/bin/env python3
"""
Doc Review CLI - Main entry point.

This is a unified CLI tool for the Doc Review system that provides
commands for configuration, deployment, operations, and development.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import typer
from rich import print as rprint

# Add project to Python path
sys.path.insert(0, str(Path(__file__).parent))

from utils import ConsoleUtils, AppConfig
from commands import setup as setup_module, config, refresh as refresh_module, tools, verify, git, delete
from commands.doctor import app as doctor_app
from commands.clean import CleanCLI

# Initialize console utilities
console_utils = ConsoleUtils()

# Create main app
app = typer.Typer(
    name="docr",
    help="Doc Review CLI - Unified tools for development and deployment",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    add_completion=False
)

# Create backend config app 
backend_config_app = typer.Typer(help="Backend configuration management")
app.add_typer(backend_config_app, name="config")

# Create verify command group
verify_app = typer.Typer(help="Verify client connections and functionality")
app.add_typer(verify_app, name="verify")

# Create git command group
git_app = typer.Typer(help="Git repository management")
app.add_typer(git_app, name="git")

# Create delete command group
delete_app = typer.Typer(help="Delete AWS resources (supports multi-delete with zellij)")
app.add_typer(delete_app, name="delete")

# Create registry command group
from commands.registry_cli import RegistrySwitchCLI
registry_cli = RegistrySwitchCLI()
app.add_typer(registry_cli.app, name="registry", help="Switch between @umd-dit and @ai-sandbox registries")

# Add doctor command group
app.add_typer(doctor_app, name="doctor", help="System health checks and diagnostics")

# Add clean command
clean_cli = CleanCLI()
app.command("clean")(clean_cli.cli)


@app.command()
def setup():
    """Initial setup - configure project root and developer settings."""
    # Ensure config directory exists
    config_file = AppConfig.CONFIG_FILE
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    if not setup_module.run_setup(config_file):
        raise typer.Exit(1)


@backend_config_app.callback(invoke_without_command=True)
def config_main(
    ctx: typer.Context,
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Show current configuration or manage frontend/backend configurations."""
    if developer_initials:
        AppConfig.set_developer_initials_override(developer_initials)
    
    if ctx.invoked_subcommand is None:
        # No subcommand - show configuration
        config.show_config()

# Add frontend config command from commands.config module
@backend_config_app.command()
def frontend(
    application: str = typer.Option(..., "--app", "-a", help="Application to configure (required)"),
    force: bool = typer.Option(False, "--force", help="Force regeneration of existing configs"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
):
    """Generate frontend configuration files."""
    if developer_initials:
        AppConfig.set_developer_initials_override(developer_initials)
    
    try:
        config.frontend(application, force)
    finally:
        # Clean up override
        AppConfig.clear_developer_initials_override()


@app.command()
def refresh():
    """Refresh configuration with latest CloudFormation stack outputs."""
    if not setup_module.check_or_setup_config(AppConfig.CONFIG_FILE):
        raise typer.Exit(1)
    refresh_module.refresh_config()


@app.command()
def tools():
    """List all available tools and their purposes."""
    tools.list_tools()


@app.command("show-urls")
def show_urls():
    """Display deployed application URLs."""
    from commands.show_urls import ShowURLsCLI
    cli = ShowURLsCLI()
    cli.display_application_urls()


@verify_app.command()
def client():
    """Verify API clients by testing connections."""
    verify.verify_client()


@git_app.command()
def clone():
    """Clone missing repositories required for the Doc Review system."""
    git.git_clone()


@delete_app.command()
def stacks(
    developer_initials: str = typer.Option(None, "--developer-initials", "-d", help="Developer initials for stacks to delete (REQUIRED for safety)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts")
):
    """Delete all CloudFormation stacks for the specified developer initials."""
    delete.delete_stacks(developer_initials, yes)


@app.command()
@delete_app.command()
def multi_stacks(
    developer_initials: str = typer.Option(..., "--developer-initials", "-d", help="Comma-separated list of developer initials (e.g. 'cm1,cm2,cm3')"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts for all deletions")
):
    """
    Delete stacks for multiple developers in parallel using zellij.
    
    This command requires zellij to be installed: brew install zellij
    
    Example:
        docr delete multi-stacks -d cm1,cm2,cm3 --yes
    
    This will create a zellij session with parallel panes for each developer's deletion.
    """
    import subprocess
    import tempfile
    from pathlib import Path
    
    # Parse developer initials
    initials_list = [i.strip() for i in developer_initials.split(',') if i.strip()]
    
    if not initials_list:
        console_utils.print_error("No developer initials provided")
        raise typer.Exit(1)
    
    # Check if zellij is installed
    try:
        subprocess.run(["zellij", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        console_utils.print_error(
            "zellij is not installed. Install it with: brew install zellij\n"
            "Or run individual deletions with: docr delete stacks -d <initials>"
        )
        raise typer.Exit(1)
    
    # Create temporary layout file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.kdl', delete=False) as f:
        layout_content = "layout {\n"
        
        for initials in initials_list:
            # Add the --yes flag if provided
            yes_flag = ' "--yes"' if yes else ''
            layout_content += f'    pane {{\n'
            layout_content += f'        command "docr"\n'
            layout_content += f'        args "delete" "stacks" "-d" "{initials}"{yes_flag}\n'
            layout_content += f'    }}\n'
        
        layout_content += "}\n"
        
        f.write(layout_content)
        layout_file = f.name
    
    try:
        # Launch zellij with the layout
        rprint(f"\n[bold]Launching zellij session to delete stacks for: {', '.join(initials_list)}[/bold]")
        rprint(f"[dim]Layout file: {layout_file}[/dim]\n")
        
        subprocess.run(["zellij", "--layout", layout_file])
        
    finally:
        # Clean up temp file
        Path(layout_file).unlink(missing_ok=True)


@app.command()
def install(
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use for deployment (overrides config)"),
    resume_from: Optional[int] = typer.Option(None, "--resume-from", help="Resume installation from a specific step"),
    skip_frontend: bool = typer.Option(False, "--skip-frontend", help="Skip frontend deployments"),
    timeout: int = typer.Option(60, "--timeout", help="Overall timeout for installation in minutes"),
    list_steps: bool = typer.Option(False, "--list-steps", help="List all installation steps without executing")
):
    """Automated installation of the entire Document Review system."""
    # Import here to avoid circular imports
    import os
    from installer import InstallCLI
    
    # Set override in environment if provided
    if developer_initials:
        try:
            AppConfig.set_developer_initials_override(developer_initials)
        except ValueError as e:
            typer.echo(f"Error: {str(e)}", err=True)
            raise typer.Exit(1)
    
    # Clear override after install completes
    try:
        cli = InstallCLI()
        cli.install(resume_from=resume_from, skip_frontend=skip_frontend, timeout=timeout, list_steps=list_steps)
    finally:
        # Clean up environment
        AppConfig.clear_developer_initials_override()


@app.command()
def version():
    """Show version information."""
    try:
        from importlib.metadata import version
        pkg_version = version("docr-cli")
        rprint(f"docr-cli version: [cyan]{pkg_version}[/cyan]")
    except Exception:
        rprint("docr-cli version: [cyan]development[/cyan]")


@app.callback()
def main(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
):
    """Doc Review CLI - Unified tools for development and deployment."""
    if verbose:
        os.environ["DOCR_DEBUG"] = "1"


# Load additional CLI modules if config exists
try:
    config_file = AppConfig.CONFIG_FILE
    if not config_file.exists():
        # Don't show warning for git commands
        if len(sys.argv) < 2 or sys.argv[1] != "git":
            console_utils.print_warning("Configuration not found. Run 'docr setup' to configure.")
    else:
        from commands.bootstrap import BootstrapCLI
        from commands.jobs import JobsCLI
        from commands.flags import FeatureFlagsCLI
        from commands.oidc_cli import OIDCCLI
        from commands.credstore_cli import CredStoreCLI
        
        bootstrap_cli = BootstrapCLI()
        jobs_cli = JobsCLI()
        flags_cli = FeatureFlagsCLI()
        oidc_cli = OIDCCLI()
        credstore_cli = CredStoreCLI()
        
        app.add_typer(bootstrap_cli.app, name="bootstrap", help="Bootstrap data management")
        app.add_typer(jobs_cli.app, name="jobs", help="Run legislative review jobs")
        app.add_typer(flags_cli.app, name="flags", help="Manage feature flags")
        app.add_typer(oidc_cli.app, name="oidc", help="OIDC client registration and management")
        app.add_typer(credstore_cli.app, name="credstore", help="Credential store management for API keys")
except FileNotFoundError as e:
    # Config file not found - this is expected for first time setup
    if "docr.toml" in str(e):
        # Only show warning if not running setup command
        if len(sys.argv) > 1 and sys.argv[1] != "setup":
            console_utils.print_warning("Configuration not found. Run 'docr setup' to configure.")
    else:
        raise
except Exception as e:
    # Only show detailed errors if verbose mode is enabled
    if os.environ.get("DOCR_DEBUG"):
        import traceback
        traceback.print_exc()
    else:
        console_utils.print_error(f"Error loading CLI modules: {str(e)}")


# Import backend and lambda config modules
try:
    from backend_config import app as backend_config_module
    from lambda_config import app as lambda_config_module
    
    # Add backend config command
    @backend_config_app.command("backend")
    def backend_command(
        component: Optional[str] = typer.Argument(None),
        all_components: bool = typer.Option(False, "--all", help="Configure all components"),
        force: bool = typer.Option(False, "--force", "-f", help="Force regeneration of existing configs"),
        developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-i", help="Developer initials to use (overrides config)")
    ):
        """Generate backend configuration files."""
        if developer_initials:
            AppConfig.set_developer_initials_override(developer_initials)
        
        try:
            # Import the function from backend_config
            from backend_config import run_backend_config
            run_backend_config(component, all_components, force)
        finally:
            # Clean up override
            AppConfig.clear_developer_initials_override()
    
    # Create lambda app and add to main app
    lambda_app = typer.Typer(help="Lambda test event configuration")
    app.add_typer(lambda_app, name="lambda")
    
    @lambda_app.command("config")
    def lambda_config_command(
        component: Optional[str] = typer.Argument(None),
        test_type: Optional[str] = typer.Option(None, "--type", "-t", help="Test event type"),
        save: bool = typer.Option(False, "--save", "-s", help="Save generated event to file"),
        list_types: bool = typer.Option(False, "--list", "-l", help="List available test types"),
    ):
        """Generate Lambda test events."""
        from lambda_config import run_lambda_config
        run_lambda_config(component, test_type, save, list_types)
        
except ImportError:
    pass


# Import and register deployment commands
try:
    from commands.fast_sync import app as fast_sync_app
    
    # Create deployment group
    deploy_app = typer.Typer(help="Deployment commands")
    app.add_typer(deploy_app, name="deploy")
    
    # Add backend deployment command
    @deploy_app.command("backend")
    def backend_deploy(
        app_name: str = typer.Option(..., "--app", help="Application or component to deploy (required)"),
        developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
    ):
        """Fast backend deployment via ECR."""
        from commands.fast_sync import run_sync_deployment
        run_sync_deployment(app_name, developer_initials)
    
    # Create build group
    build_app = typer.Typer(help="Build commands")
    app.add_typer(build_app, name="build")
    
    # Add frontend deploy command
    @deploy_app.command("frontend")
    def frontend_deploy(
        app: str = typer.Option(..., "--app", help="Application to deploy (e.g., legislative-review)"),
        full: bool = typer.Option(False, "--full", "-f", help="Include CloudFormation infrastructure updates (SAM deploy)"),
        developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    ):
        """Deploy frontend to S3/CloudFront."""
        from frontend_deploy import FrontendDeployCLI
        
        # Set developer initials override if provided
        if developer_initials:
            try:
                AppConfig.set_developer_initials_override(developer_initials)
            except ValueError as e:
                typer.echo(f"Error: {str(e)}", err=True)
                raise typer.Exit(1)
        
        try:
            cli = FrontendDeployCLI()
            # Call the deploy method directly with parameters
            cli.run_deploy(app, not full, verbose)  # Note: inverting full to s3_only
        finally:
            # Clean up environment
            AppConfig.clear_developer_initials_override()
    
    # Add frontend build command
    @build_app.command("frontend")
    def frontend_build(
        component: str = typer.Argument(..., help="Component to build (workspaces, jobs, cost)"),
        app: str = typer.Option(..., "--app", help="Application to update with new component version (e.g., legislative-review)"),
        developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
    ):
        """Build and publish frontend components to @ai-sandbox registry."""
        from frontend_build import FrontendBuildCLI
        
        # Set developer initials override if provided
        if developer_initials:
            try:
                AppConfig.set_developer_initials_override(developer_initials)
            except ValueError as e:
                typer.echo(f"Error: {str(e)}", err=True)
                raise typer.Exit(1)
        
        try:
            cli = FrontendBuildCLI()
            cli.run_build(component, app)
        finally:
            # Clean up environment
            AppConfig.clear_developer_initials_override()
    
except ImportError as e:
    if os.environ.get("DOCR_DEBUG"):
        import traceback
        traceback.print_exc()
    pass  # Deployment commands not available without config


if __name__ == "__main__":
    app()