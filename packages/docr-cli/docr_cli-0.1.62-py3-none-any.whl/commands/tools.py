"""List available tools and commands."""
from rich.table import Table
from rich import print as rprint

from utils import ConsoleUtils


def list_tools():
    """Display all available CLI tools and their purposes."""
    console_utils = ConsoleUtils()
    
    # Create tools table
    table = Table(title="[bold]Doc Review CLI Tools[/bold]")
    table.add_column("Command", style="cyan", width=25)
    table.add_column("Purpose", style="white")
    table.add_column("Example", style="dim")
    
    # Configuration & Setup
    table.add_row("docr setup", "Initial setup and configuration", "docr setup")
    table.add_row("docr install", "Automated full system deployment", "docr install")
    table.add_row("docr config", "Show current configuration", "docr config")
    table.add_row("docr config backend", "Generate backend samconfig files", "docr config backend --all")
    table.add_row("docr refresh", "Update config from AWS stacks", "docr refresh")
    
    # Deployment
    table.add_row("", "", "")  # Empty row for spacing
    table.add_row("[bold]Deployment[/bold]", "", "")
    table.add_row("docr deploy backend", "Fast Lambda deployment via ECR", "docr deploy backend legislative-review")
    table.add_row("docr deploy frontend", "Deploy frontend to S3/CloudFront", "docr deploy frontend --full-deploy")
    table.add_row("docr build frontend", "Build & publish React components", "docr build frontend --components all")
    
    # Operations
    table.add_row("", "", "")
    table.add_row("[bold]Operations[/bold]", "", "")
    table.add_row("docr bootstrap", "Load initial data", "docr bootstrap all")
    table.add_row("docr jobs", "Run legislative review jobs", "docr jobs sync --app legislative-review --session 2025RS")
    table.add_row("docr flags", "Manage feature flags", "docr flags sync --components legislative-review,workspaces")
    
    # Security & Auth
    table.add_row("", "", "")
    table.add_row("[bold]Security & Auth[/bold]", "", "")
    table.add_row("docr oidc", "OIDC client management", "docr oidc register all")
    table.add_row("docr credstore", "Manage API keys", "docr credstore add")
    
    # Development
    table.add_row("", "", "")
    table.add_row("[bold]Development[/bold]", "", "")
    table.add_row("docr verify client", "Test API client connections", "docr verify client")
    table.add_row("docr git clone", "Clone missing repositories", "docr git clone")
    table.add_row("docr lambda config", "Lambda test configuration", "docr lambda config")
    
    # Cleanup
    table.add_row("", "", "")
    table.add_row("[bold]Cleanup[/bold]", "", "")
    table.add_row("docr delete stacks", "Delete all developer stacks", "docr delete stacks")
    
    # Help
    table.add_row("", "", "")
    table.add_row("[bold]Help[/bold]", "", "")
    table.add_row("docr --help", "Show main help", "docr --help")
    table.add_row("docr <command> --help", "Show command-specific help", "docr jobs --help")
    table.add_row("docr version", "Show version information", "docr version")
    
    console_utils.console.print(table)
    
    rprint("\n[bold]Getting Started:[/bold]")
    rprint("• First time setup: [cyan]docr setup[/cyan]")
    rprint("• Check configuration: [cyan]docr config[/cyan]")
    rprint("• Refresh config after frontend deployment: [cyan]docr refresh[/cyan]")
    rprint("• Bootstrap all components: [cyan]docr bootstrap all[/cyan]")
    rprint("• Register OIDC for current component: [cyan]docr oidc register[/cyan]")
    rprint("• Run a quick sync job: [cyan]docr jobs sync --app legislative-review --session 2025RS[/cyan]")
    rprint(f"• Deploy backend changes: [cyan]docr deploy backend <app-name>[/cyan]")
    rprint("• Deploy frontend changes: [cyan]docr deploy frontend[/cyan]")