#!/usr/bin/env python3
"""
Registry switch CLI for switching between @umd-dit and @ai-sandbox namespaces.
Handles component package.json updates and frontend dependency updates.
"""
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
import typer
from rich.table import Table

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, AppConfig


class RegistrySwitchCLI(BaseCLI):
    """Registry namespace switching CLI."""
    
    # Registry configurations
    REGISTRIES = {
        "production": {
            "namespace": "@umd-dit",
            "version_pattern": "semantic",  # 1.0.0, 1.1.0, etc.
            "description": "Production/Bamboo CI registry"
        },
        "development": {
            "namespace": "@ai-sandbox", 
            "version_pattern": "alpha",     # 1.0.1-alpha.X
            "description": "Developer sandbox registry"
        }
    }
    
    def __init__(self):
        super().__init__(
            name="registry-switch",
            help_text="Switch between @umd-dit and @ai-sandbox registry namespaces.\n\n"
                     "This tool updates component package.json files and frontend dependencies\n"
                     "to use the appropriate registry for production (Bamboo CI) or development.",
            require_config=False,
            setup_python_path=False
        )
        
        # Get project root
        self.doc_review_root = AppConfig.get_project_root()
        
        # Component paths
        self.component_paths = {
            "workspaces": "aisolutions-workspaces-serverless/workspaces-component-frontend",
            "jobs": "aisolutions-jobsmodule-serverless/jobs-component-frontend", 
            "cost": "aisolutions-costsmodule-serverless/cost-component-frontend"
        }
        
        # Frontend path
        self.frontend_path = "aisolutions-docreview-serverless/legislative-review-frontend"
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        self.app.command()(self.switch)
        self.app.command()(self.status)
    
    def switch(
        self, 
        mode: str = typer.Argument(help="Registry mode: 'production' (@umd-dit) or 'development' (@ai-sandbox)"),
        dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be changed without making changes"),
        verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
    ):
        """Switch all components and frontend to use specified registry namespace.
        
        Examples:
            Switch to production registry for Bamboo CI:
                docr registry switch production
                
            Switch to development registry for sandbox:
                docr registry switch development
                
            Preview changes without applying:
                docr registry switch production --dry-run
        """
        if mode not in self.REGISTRIES:
            self.console_utils.print_error(
                f"Invalid mode: {mode}\n"
                f"Available modes: {', '.join(self.REGISTRIES.keys())}"
            )
            raise typer.Exit(1)
        
        self.run_switch(mode, dry_run, verbose)
    
    def run_switch(self, mode: str, dry_run: bool, verbose: bool):
        """Execute the registry switch."""
        registry_config = self.REGISTRIES[mode]
        namespace = registry_config["namespace"]
        
        self.console_utils.print_info(f"Switching to {mode} mode ({namespace})")
        if dry_run:
            self.console_utils.print_warning("DRY RUN MODE - No changes will be made")
        
        changes = []
        
        # Step 1: Update component package.json files
        self.console_utils.print_step(1, 3, f"Updating component package.json files to {namespace}...")
        component_changes = self._update_components(mode, dry_run, verbose)
        changes.extend(component_changes)
        
        # Step 2: Update frontend dependencies
        self.console_utils.print_step(2, 3, "Updating frontend dependencies...")
        frontend_changes = self._update_frontend_dependencies(mode, dry_run, verbose)
        changes.extend(frontend_changes)
        
        # Step 3: Display summary
        self.console_utils.print_step(3, 3, "Summary of changes...")
        self._display_changes_summary(changes, mode, dry_run)
        
        if not dry_run:
            self.console_utils.print_success(f"Successfully switched to {mode} mode ({namespace})")
        else:
            self.console_utils.print_info(f"Would switch to {mode} mode ({namespace})")
    
    def _update_components(self, mode: str, dry_run: bool, verbose: bool) -> List[Tuple[str, str, str, str]]:
        """Update component package.json files."""
        changes = []
        namespace = self.REGISTRIES[mode]["namespace"]
        
        for component, relative_path in self.component_paths.items():
            package_json_path = self.doc_review_root / relative_path / "package.json"
            
            if not package_json_path.exists():
                self.console_utils.print_warning(f"Package.json not found: {package_json_path}")
                continue
            
            # Read current package.json
            with open(package_json_path) as f:
                package_data = json.load(f)
            
            old_name = package_data.get("name", "")
            old_version = package_data.get("version", "")
            
            # Generate new name and version
            new_name = f"{namespace}/{component}-component-react"
            new_version = self._get_appropriate_version(component, mode, old_version)
            
            # Track changes
            if old_name != new_name or old_version != new_version:
                changes.append((f"Component: {component}", old_name, new_name, f"{old_version} → {new_version}"))
            
            # Apply changes if not dry run
            if not dry_run and (old_name != new_name or old_version != new_version):
                package_data["name"] = new_name
                package_data["version"] = new_version
                
                with open(package_json_path, "w") as f:
                    json.dump(package_data, f, indent=2)
                    f.write("\n")
                
                if verbose:
                    self.console_utils.print_info(f"Updated {component}: {old_name} → {new_name}")
        
        return changes
    
    def _update_frontend_dependencies(self, mode: str, dry_run: bool, verbose: bool) -> List[Tuple[str, str, str, str]]:
        """Update frontend dependencies."""
        changes = []
        namespace = self.REGISTRIES[mode]["namespace"]
        
        frontend_package_path = self.doc_review_root / self.frontend_path / "package.json"
        
        if not frontend_package_path.exists():
            self.console_utils.print_error(f"Frontend package.json not found: {frontend_package_path}")
            return changes
        
        # Read frontend package.json
        with open(frontend_package_path) as f:
            package_data = json.load(f)
        
        deps = package_data.get("dependencies", {})
        
        # Update component dependencies
        for component in self.component_paths.keys():
            dep_key = f"@umd-dit/{component}-component-react"
            
            if dep_key in deps:
                old_value = deps[dep_key]
                
                if mode == "production":
                    # Use direct dependency
                    new_value = self._get_appropriate_version(component, mode)
                elif mode == "development":
                    # Use npm alias
                    alpha_version = self._get_appropriate_version(component, mode)
                    new_value = f"npm:@ai-sandbox/{component}-component-react@{alpha_version}"
                
                if old_value != new_value:
                    changes.append((f"Frontend: {dep_key}", old_value, new_value, ""))
                    
                    if not dry_run:
                        deps[dep_key] = new_value
                        if verbose:
                            self.console_utils.print_info(f"Updated frontend dep: {dep_key}")
        
        # Write updated frontend package.json
        if not dry_run and changes:
            with open(frontend_package_path, "w") as f:
                json.dump(package_data, f, indent=2)
                f.write("\n")
        
        return changes
    
    def _get_appropriate_version(self, component: str, mode: str, current_version: str = None) -> str:
        """Get appropriate version for component based on mode."""
        if mode == "production":
            return "1.0.0"  # Semantic version for production
        elif mode == "development":
            # For development, try to preserve current alpha version or use a default
            if current_version and "alpha" in current_version:
                return current_version
            else:
                # Default alpha versions - these would typically be the latest from CodeArtifact
                defaults = {
                    "workspaces": "1.0.1-alpha.9",
                    "jobs": "1.0.1-alpha.86", 
                    "cost": "1.0.1-alpha.97"
                }
                return defaults.get(component, "1.0.1-alpha.1")
        
        return "1.0.0"
    
    def _display_changes_summary(self, changes: List[Tuple[str, str, str, str]], mode: str, dry_run: bool):
        """Display summary of changes."""
        if not changes:
            self.console_utils.print_info("No changes needed - already in correct state")
            return
        
        action = "Would make" if dry_run else "Made"
        self.console_utils.print_info(f"{action} {len(changes)} changes:")
        
        table = Table(title=f"Registry Switch to {mode.title()} Mode")
        table.add_column("Component/Frontend", style="cyan")
        table.add_column("Old Value", style="red")
        table.add_column("New Value", style="green") 
        table.add_column("Version Change", style="yellow")
        
        for item, old_val, new_val, version_info in changes:
            table.add_row(item, old_val, new_val, version_info)
        
        self.console.print(table)
    
    def status(self):
        """Show current registry configuration across all components and frontend."""
        self.show_status()
    
    def show_status(self):
        """Show current registry status."""
        self.console_utils.print_info("Current Registry Configuration")
        
        table = Table(title="Component Registry Status")
        table.add_column("Component", style="cyan")
        table.add_column("Package Name", style="white")
        table.add_column("Version", style="yellow")
        table.add_column("Registry", style="green")
        
        # Check components
        for component, relative_path in self.component_paths.items():
            package_json_path = self.doc_review_root / relative_path / "package.json"
            
            if package_json_path.exists():
                with open(package_json_path) as f:
                    package_data = json.load(f)
                
                name = package_data.get("name", "Unknown")
                version = package_data.get("version", "Unknown")
                
                if "@umd-dit" in name:
                    registry = "@umd-dit (Production)"
                elif "@ai-sandbox" in name:
                    registry = "@ai-sandbox (Development)"
                else:
                    registry = "Unknown"
                
                table.add_row(component.title(), name, version, registry)
            else:
                table.add_row(component.title(), "Not Found", "N/A", "N/A")
        
        self.console.print(table)
        
        # Check frontend dependencies
        frontend_package_path = self.doc_review_root / self.frontend_path / "package.json"
        if frontend_package_path.exists():
            with open(frontend_package_path) as f:
                package_data = json.load(f)
            
            deps = package_data.get("dependencies", {})
            
            frontend_table = Table(title="Frontend Dependencies")
            frontend_table.add_column("Dependency", style="cyan")
            frontend_table.add_column("Value", style="white")
            frontend_table.add_column("Type", style="green")
            
            for component in self.component_paths.keys():
                dep_key = f"@umd-dit/{component}-component-react"
                if dep_key in deps:
                    value = deps[dep_key]
                    if value.startswith("npm:@ai-sandbox"):
                        dep_type = "npm alias → @ai-sandbox"
                    elif value.startswith("@umd-dit"):
                        dep_type = "Direct @umd-dit"
                    else:
                        dep_type = "Other"
                    
                    frontend_table.add_row(dep_key, value, dep_type)
            
            self.console.print(frontend_table)


def main():
    """Main entry point."""
    cli = RegistrySwitchCLI()
    cli.run()


if __name__ == "__main__":
    main()