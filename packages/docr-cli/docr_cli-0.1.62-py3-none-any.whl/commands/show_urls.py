#!/usr/bin/env python3
"""Show deployed application URLs."""

from pathlib import Path
from typing import Dict, Optional
from rich.table import Table
from rich import box
import sys

# Add utils to path before other imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils import BaseCLI, AppConfig
from utils.shared_console import get_shared_console


class ShowURLsCLI(BaseCLI):
    """Show deployed application URLs."""
    
    def __init__(self):
        super().__init__(
            name="show-urls",
            help_text="Display deployed application URLs",
            require_config=True
        )
        self.console = get_shared_console()
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.callback(invoke_without_command=True)
        def show_urls():
            """Display all deployed application URLs."""
            self.display_application_urls()
    
    def display_application_urls(self):
        """Display URLs for all deployed applications."""
        # First refresh config to ensure we have latest data
        self.console.print("[dim]Refreshing configuration...[/dim]")
        from commands.refresh import refresh_config
        refresh_config()
        
        # Now load the updated config
        config = AppConfig.load_config()
        
        # Get stage (default to sandbox)
        stage = "sandbox"  # Could be made configurable later
        
        # Define applications to show
        apps = [
            {
                'name': 'Legislative Review Application',
                'config_key': 'legislative-review',
                'config_section': 'applications'
            },
            {
                'name': 'OIDC Manager Application', 
                'config_key': 'oidc-manager',
                'config_section': 'applications'
            }
        ]
        
        # Create table
        table = Table(
            title="🌐 Deployed Application URLs",
            box=box.ROUNDED,
            show_lines=True,
            title_style="bold cyan"
        )
        table.add_column("Application", style="green", width=35)
        table.add_column("URL", style="blue", width=80)
        
        # Add URLs to table
        found_urls = False
        for app in apps:
            app_config = config.get(app['config_section'], {}).get(app['config_key'], {})
            url = app_config.get(f'stage_{stage}_frontend_url')
            
            if url:
                found_urls = True
                # Make URL clickable in terminals that support it
                clickable_url = f"[link={url}]{url}[/link]"
                table.add_row(app['name'], clickable_url)
            else:
                table.add_row(app['name'], "[dim]Not deployed[/dim]")
        
        # Display table
        self.console.print("\n")
        self.console.print(table)
        
        if found_urls:
            self.console.print("\n[bold green]✅ Applications are ready![/bold green]")
            self.console.print("[dim]Click the URLs above or copy/paste them into your browser[/dim]")
            
            # Show default credentials hint
            self.console.print("\n[bold]Default Credentials:[/bold]")
            self.console.print("Username: [cyan]admin@umd.edu[/cyan]")
            self.console.print("Password: [cyan]password[/cyan]")
        else:
            self.console.print("\n[yellow]⚠️  No deployed applications found[/yellow]")
            self.console.print("[dim]If applications are deployed, the configuration refresh may have failed[/dim]")
        
        self.console.print("\n")


def main():
    """Main entry point."""
    cli = ShowURLsCLI()
    cli.run()


if __name__ == "__main__":
    main()