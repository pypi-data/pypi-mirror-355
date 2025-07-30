#!/usr/bin/env python3
"""
Rich console utilities for consistent output across CLI scripts.
Provides standardized formatting, tables, and progress indicators.
"""
import sys
from typing import Dict, List, Tuple, Optional, Any
from rich import print
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
import typer
from .shared_console import get_shared_console


class ConsoleUtils:
    """Rich console utilities for consistent output."""
    
    def __init__(self):
        """Initialize console utilities."""
        self.console = get_shared_console()
    
    def create_status_table(self, title: str, data: Dict[str, Any], 
                          key_style: str = "cyan") -> Table:
        """
        Create standardized status table.
        
        Args:
            title: Table title
            data: Dictionary of key-value pairs to display
            key_style: Style for the key column
            
        Returns:
            Rich Table object
        """
        table = Table(title=title)
        table.add_column("Field", style=key_style)
        table.add_column("Value")
        
        for key, value in data.items():
            # Convert underscores to spaces and title case
            display_key = key.replace('_', ' ').title()
            table.add_row(display_key, str(value))
        
        return table
    
    def print_success(self, message: str, prefix: str = "✅") -> None:
        """Print success message with checkmark."""
        self.console.print(f"[green]{prefix} {message}[/green]")
    
    def print_error(self, message: str, exit_code: Optional[int] = None,
                   prefix: str = "❌") -> None:
        """
        Print error and optionally exit.
        
        Args:
            message: Error message
            exit_code: If provided, exit with this code
            prefix: Prefix character/emoji
        """
        self.console.print(f"[red]{prefix} {message}[/red]")
        if exit_code is not None:
            raise typer.Exit(exit_code)
    
    def print_warning(self, message: str, prefix: str = "⚠️") -> None:
        """Print warning message."""
        self.console.print(f"[yellow]{prefix} {message}[/yellow]")
    
    def print_info(self, message: str, prefix: str = "ℹ️") -> None:
        """Print info message."""
        self.console.print(f"[blue]{prefix} {message}[/blue]")
    
    def create_summary_table(self, results: List[Tuple[str, bool]], 
                           title: str = "Summary") -> Table:
        """
        Create summary table with pass/fail status.
        
        Args:
            results: List of (name, success) tuples
            title: Table title
            
        Returns:
            Rich Table with formatted results
        """
        table = Table(title=title)
        table.add_column("Component", style="cyan")
        table.add_column("Status")
        
        all_success = True
        for name, success in results:
            if success:
                status = "[green]✅ Passed[/green]"
            else:
                status = "[red]❌ Failed[/red]"
                all_success = False
            table.add_row(name, status)
        
        return table
    
    def get_progress(self, description: str = "Processing...") -> Progress:
        """
        Get configured progress bar.
        
        Args:
            description: Default description for tasks
            
        Returns:
            Rich Progress object
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeRemainingColumn(),
            console=self.console
        )
    
    def print_panel(self, content: str, title: str = "", 
                   style: str = "blue") -> None:
        """
        Print content in a styled panel.
        
        Args:
            content: Panel content
            title: Panel title
            style: Panel border style
        """
        panel = Panel(content, title=title, style=style)
        self.console.print(panel)
    
    def prompt_confirm(self, message: str, default: bool = False) -> bool:
        """
        Prompt for confirmation with consistent styling.
        
        Args:
            message: Confirmation message
            default: Default value if user just presses enter
            
        Returns:
            User's choice
        """
        return typer.confirm(message, default=default)
    
    def create_config_table(self, config: Dict[str, str], 
                          title: str = "Configuration") -> Table:
        """
        Create table specifically for configuration display.
        
        Args:
            config: Configuration dictionary
            title: Table title
            
        Returns:
            Formatted configuration table
        """
        table = Table(title=title)
        table.add_column("Variable", style="cyan")
        table.add_column("Value")
        table.add_column("Type", style="dim")
        
        # Group by type
        api_vars = {k: v for k, v in config.items() if k.endswith("_API_URL")}
        other_vars = {k: v for k, v in config.items() 
                     if not k.endswith("_API_URL")}
        
        # Add API URLs
        for key, value in sorted(api_vars.items()):
            table.add_row(key, value or "[dim]Not set[/dim]", "API")
        
        # Add other variables
        for key, value in sorted(other_vars.items()):
            table.add_row(key, value or "[dim]Not set[/dim]", "Config")
        
        return table
    
    def print_step(self, step_num: int, total_steps: int, 
                  description: str) -> None:
        """
        Print a numbered step in a process.
        
        Args:
            step_num: Current step number
            total_steps: Total number of steps
            description: Step description
        """
        self.console.print(
            f"[bold blue]Step {step_num}/{total_steps}:[/bold blue] {description}"
        )
    
    def create_list_table(self, items: List[Dict[str, Any]], 
                         title: str, columns: List[str]) -> Table:
        """
        Create a table from a list of dictionaries.
        
        Args:
            items: List of dictionaries
            title: Table title
            columns: Column names to display
            
        Returns:
            Formatted table
        """
        table = Table(title=title)
        
        # Add columns
        for col in columns:
            style = "cyan" if columns.index(col) == 0 else None
            table.add_column(col.replace('_', ' ').title(), style=style)
        
        # Add rows
        for item in items:
            row = []
            for col in columns:
                value = item.get(col, '')
                # Format boolean values
                if isinstance(value, bool):
                    value = "✓" if value else "✗"
                row.append(str(value))
            table.add_row(*row)
        
        return table
    
    def format_error_details(self, error: Exception, 
                           show_traceback: bool = False) -> str:
        """
        Format error details for display.
        
        Args:
            error: Exception object
            show_traceback: Whether to include full traceback
            
        Returns:
            Formatted error message
        """
        error_text = f"[red]Error: {type(error).__name__}[/red]\n"
        error_text += f"[red]{str(error)}[/red]"
        
        if show_traceback:
            import traceback
            error_text += "\n\n[dim]Traceback:[/dim]\n"
            error_text += f"[dim]{traceback.format_exc()}[/dim]"
        
        return error_text
    
    @staticmethod
    def create_status_indicator(status: str) -> str:
        """
        Create colored status indicator.
        
        Args:
            status: Status string
            
        Returns:
            Colored status with emoji
        """
        status_lower = status.lower()
        
        if status_lower in ['success', 'completed', 'active', 'enabled']:
            return f"[green]✅ {status}[/green]"
        elif status_lower in ['failed', 'error', 'disabled']:
            return f"[red]❌ {status}[/red]"
        elif status_lower in ['pending', 'in_progress', 'processing']:
            return f"[yellow]⏳ {status}[/yellow]"
        elif status_lower in ['warning', 'degraded']:
            return f"[yellow]⚠️ {status}[/yellow]"
        else:
            return f"[dim]{status}[/dim]"
    
    @staticmethod
    def error(message: str, exit_code: Optional[int] = None) -> None:
        """Print error message and optionally exit."""
        console = get_shared_console()
        console.print(f"[red]❌ {message}[/red]")
        if exit_code is not None:
            raise typer.Exit(exit_code)
    
    @staticmethod
    def success(message: str) -> None:
        """Print success message."""
        console = get_shared_console()
        console.print(f"[green]✅ {message}[/green]")
    
    @staticmethod
    def warning(message: str) -> None:
        """Print warning message."""
        console = get_shared_console()
        console.print(f"[yellow]⚠️ {message}[/yellow]")
    
    @staticmethod
    def info(message: str) -> None:
        """Print info message."""
        console = get_shared_console()
        console.print(f"[blue]ℹ️ {message}[/blue]")
    
    @staticmethod
    def header(text: str, style: str = "bold") -> None:
        """Print a header."""
        console = get_shared_console()
        console.print(f"[{style}]{text}[/{style}]")
    
    @staticmethod
    def create_table(title: Optional[str] = None) -> Table:
        """Create a new table with optional title."""
        return Table(title=title)