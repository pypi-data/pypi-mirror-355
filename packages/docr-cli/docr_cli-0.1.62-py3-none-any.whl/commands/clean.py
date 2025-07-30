#!/usr/bin/env python3
"""Clean command for removing generated files and directories from doc-review project."""

import shutil
from pathlib import Path
from typing import Tuple

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from utils.base_cli import BaseCLI

console = Console()


class CleanCLI(BaseCLI):
    """Clean generated files and directories from doc-review project."""

    def __init__(self):
        """Initialize Clean CLI."""
        super().__init__(
            name="clean",
            help_text="Clean generated files and directories from doc-review project",
            require_config=False
        )
        self.project_root = None  # Will be set when command runs
        self.total_deleted_files = 0
        self.total_deleted_dirs = 0
        self.total_space_freed = 0

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes."""
        total = 0
        try:
            for entry in path.rglob("*"):
                if entry.is_file():
                    total += entry.stat().st_size
        except (OSError, PermissionError):
            pass
        return total

    def _format_bytes(self, size_bytes: int) -> str:
        """Format bytes to human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"

    def _delete_file(self, file_path: Path) -> None:
        """Safely delete a file if it exists."""
        if file_path.exists() and file_path.is_file():
            console.print(f"  Removing: {file_path}")
            file_path.unlink()
            self.total_deleted_files += 1

    def _delete_directory(self, dir_path: Path) -> None:
        """Delete a directory and track its size."""
        if dir_path.exists() and dir_path.is_dir():
            size = self._get_directory_size(dir_path)
            self.total_space_freed += size
            console.print(f"  Removing: {dir_path} ({self._format_bytes(size)})")
            shutil.rmtree(dir_path, ignore_errors=True)
            self.total_deleted_dirs += 1

    def _clean_configuration_files(self) -> None:
        """Clean frontend and backend configuration files."""
        console.print("\n[bold]📁 Cleaning Configuration Files[/bold]")
        console.print("─" * 40)

        # Clean frontend .env.production files
        frontend_patterns = ["*-frontend", "legislative-review-*", "oidc-manager-*"]
        for pattern in frontend_patterns:
            for frontend_dir in self.project_root.glob(f"**/{pattern}"):
                if "node_modules" in str(frontend_dir):
                    continue
                console.print(f"\n🌐 {frontend_dir}:")
                self._delete_file(frontend_dir / ".env.production")
                self._delete_file(frontend_dir / "config" / "sandbox" / ".env.production")

        # Clean backend config files
        for backend_dir in self.project_root.glob("**/*-backend"):
            if "node_modules" in str(backend_dir):
                continue
            console.print(f"\n⚙️  {backend_dir}:")
            self._delete_file(backend_dir / "samconfig.toml")
            self._delete_file(backend_dir / "config" / "config.sandbox")

        # Clean component backends
        component_patterns = [
            "*/cost-component-backend",
            "*/jobs-component-backend",
            "*/workspaces-component-backend",
        ]
        for pattern in component_patterns:
            for component_dir in self.project_root.glob(pattern):
                console.print(f"\n📦 {component_dir}:")
                self._delete_file(component_dir / "samconfig.toml")
                self._delete_file(component_dir / "developer.config.env")

    def _clean_sam_builds(self) -> None:
        """Clean SAM build directories."""
        console.print("\n[bold]📁 Cleaning SAM Build Directories[/bold]")
        console.print("─" * 40)

        for sam_dir in self.project_root.glob("**/.aws-sam"):
            self._delete_directory(sam_dir)

    def _clean_npm_files(self) -> None:
        """Clean .npmrc and package-lock.json files."""
        console.print("\n[bold]📁 Cleaning .npmrc Files[/bold]")
        console.print("─" * 40)

        for npmrc in self.project_root.glob("**/.npmrc"):
            if "node_modules" not in str(npmrc):
                self._delete_file(npmrc)

        console.print("\n[bold]📁 Cleaning package-lock.json Files[/bold]")
        console.print("─" * 40)

        for lock_file in self.project_root.glob("**/package-lock.json"):
            if "node_modules" not in str(lock_file):
                self._delete_file(lock_file)

    def _clean_node_modules(self) -> None:
        """Clean node_modules directories."""
        console.print("\n[bold]📁 Cleaning node_modules Directories[/bold]")
        console.print("─" * 40)

        # Find all frontend directories with node_modules
        for frontend_dir in self.project_root.glob("**/*-frontend"):
            if "node_modules" in str(frontend_dir):
                continue
            node_modules = frontend_dir / "node_modules"
            if node_modules.exists():
                console.print(f"\n🌐 {frontend_dir}:")
                self._delete_directory(node_modules)

        # Special case for oidc-oidcwebcomponent
        oidc_component = self.project_root / "oidc-oidcwebcomponent" / "node_modules"
        if oidc_component.exists():
            console.print("\n🌐 ./oidc-oidcwebcomponent:")
            self._delete_directory(oidc_component)

    def _show_summary(self) -> None:
        """Show cleanup summary."""
        console.print("\n" + "=" * 60)
        console.print("[bold green]✅ Cleanup Complete![/bold green]")
        
        summary_table = Table(show_header=False, box=None)
        summary_table.add_column(style="cyan")
        summary_table.add_column(style="white")
        
        summary_table.add_row("Files deleted:", f"{self.total_deleted_files}")
        summary_table.add_row("Directories removed:", f"{self.total_deleted_dirs}")
        summary_table.add_row("Space freed:", self._format_bytes(self.total_space_freed))
        
        console.print(summary_table)
        
        console.print("\n[bold]Next steps:[/bold]")
        console.print("  1. Run 'docr config backend --all' to regenerate backend configs")
        console.print("  2. Deploy backends with 'sam deploy'")
        console.print("  3. Run 'docr oidc register all' to setup OIDC and frontend configs")
        console.print("  4. Run 'npm install' in frontend directories to reinstall dependencies")

    def cli(
        self,
        yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompt and proceed with cleanup")
    ) -> None:
        """Clean all generated files in doc-review project.

        This command performs a clean installation by removing:
        - Configuration files (.env.production, samconfig.toml, config.sandbox)
        - SAM build directories (.aws-sam)
        - NPM files (.npmrc, package-lock.json)
        - Node modules directories

        WARNING: This will delete all local configuration and require full reconfiguration.
        """
        # Set project root when command runs
        try:
            from utils import AppConfig
            config = AppConfig.load_config()
            self.project_root = Path(config.get("project_root", "."))
        except:
            # Fallback to current directory's parent if config not available
            self.project_root = Path(".").resolve().parent
            
        console.print(Panel.fit(
            "[bold]🧹 Doc Review Cleanup Tool[/bold]\n"
            f"Working directory: {self.project_root}",
            border_style="blue"
        ))

        if not yes:
            console.print("\n[yellow]⚠️  WARNING:[/yellow] This command will delete:")
            console.print("  • All .env.production files")
            console.print("  • All samconfig.toml files")
            console.print("  • All config.sandbox files")
            console.print("  • All developer.config.env files")
            console.print("  • All .aws-sam build directories")
            console.print("  • All .npmrc files")
            console.print("  • All package-lock.json files")
            console.print("  • All node_modules directories")
            console.print("\nThis will require full reconfiguration of your development environment.")
            
            if not typer.confirm("\nDo you want to continue?", default=False):
                console.print("[red]Cleanup cancelled.[/red]")
                return

        # Perform cleanup
        self._clean_configuration_files()
        self._clean_sam_builds()
        self._clean_npm_files()
        self._clean_node_modules()
        self._show_summary()


def main():
    """Entry point for clean command."""
    cli = CleanCLI()
    cli.cli()


if __name__ == "__main__":
    main()