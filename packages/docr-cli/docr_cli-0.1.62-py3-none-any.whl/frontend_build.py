#!/usr/bin/env python3
"""
Frontend component build and publish CLI.
Automates building and publishing frontend components to AWS CodeArtifact.

This tool replaces the individual build-alpha-workspace.sh scripts with a unified
interface that works for all frontend components (workspaces, jobs, cost).
"""
import os
import json
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import typer
from rich.table import Table

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, CommandUtils, ConsoleUtils


class FrontendBuildCLI(BaseCLI):
    """Frontend component build and publish CLI."""
    
    # Registry configurations
    REGISTRIES = {
        "@ai-sandbox": {
            "url": "https://umd-dit-ai-team-265858620073.d.codeartifact.us-east-1.amazonaws.com/npm/ai-team-artifacts/",
            "repository": "ai-team-artifacts",
            "domain": "umd-dit-ai-team",
            "domain_owner": "265858620073"
        },
        "@umd-dit": {
            "url": "https://umd-495686535940.d.codeartifact.us-east-1.amazonaws.com/npm/ese-snapshot/",
            "repository": "ese-snapshot",
            "domain": "umd",
            "domain_owner": "495686535940"
        }
    }
    
    def __init__(self):
        super().__init__(
            name="frontend-build",
            help_text="Build and publish frontend components to AWS CodeArtifact.\n\n"
                     "By default, publishes to @ai-sandbox registry for developer use.\n"
                     "For dev/qa/prod apphosting, use --registry @umd-dit to publish to ESE snapshot.",
            require_config=False,  # We don't need backend config for frontend builds
            setup_python_path=False  # Don't require config for setup
        )
        
        # Get project root from config
        from utils import AppConfig
        self.doc_review_root = AppConfig.get_project_root()
        
        # Frontend directories will be determined when needed
        self.active_frontend_dir = None
        
        # Get component paths and packages dynamically
        self.components = AppConfig.get_all_component_paths()
        self.package_names = AppConfig.get_all_component_npm_packages()
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        # Store self reference for closures
        cli = self
        
        @self.app.command()
        def build(
            component: str = typer.Argument(..., help="Component to build (workspaces, jobs, cost)"),
            app: str = typer.Option(..., "--app", help="Application to update with new component version (e.g., legislative-review)"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
        ):
            """Build and publish a frontend component to AWS CodeArtifact.
            
            This command automates the full build process:
            1. Installs dependencies
            2. Ensures component is in development mode
            3. Checks component lint
            4. Tests the build
            5. Bumps the alpha version
            6. Builds and publishes to @ai-sandbox CodeArtifact
            7. Updates application frontend to use the new version
            
            Examples:
                Build workspaces component for legislative-review:
                    frontend-build build workspaces --app legislative-review
                    
                Build with different developer initials:
                    frontend-build build jobs --app legislative-review -d abc
                    
            """
            # When running frontend_build.py directly
            from utils import AppConfig
            
            # Set developer initials override if provided
            if developer_initials:
                try:
                    AppConfig.set_developer_initials_override(developer_initials)
                except ValueError as e:
                    cli.console_utils.print_error(f"Error: {str(e)}", exit_code=1)
            
            try:
                cli.run_build(component, app)
            finally:
                # Clean up environment
                AppConfig.clear_developer_initials_override()
    
    def run_build(self, component: str, app: str):
        """Run the build process for a component."""
        # Always verbose mode
        verbose = True
        # Always use @ai-sandbox registry
        registry = "@ai-sandbox"
        
        # Validate component
        if component not in self.components:
            self.console_utils.print_error(
                f"Unknown component: {component}\n"
                f"Available components: {', '.join(self.components.keys())}",
                exit_code=1
            )
        
        # Get component directory
        component_dir = self.doc_review_root / self.components[component]
        if not component_dir.exists():
            self.console_utils.print_error(
                f"Component directory not found: {component_dir}",
                exit_code=1
            )
        
        # Change to component directory
        os.chdir(component_dir)
        
        # Step 0: Run npm install
        self.console_utils.print_step(0, 7, f"Installing dependencies for {component}...")
        self.console_utils.print_info(f"Running npm install in {component_dir}")
        install_result = subprocess.run(["npm", "install"], capture_output=False)
        if install_result.returncode != 0:
            self.console_utils.print_error("npm install failed!", exit_code=1)
        else:
            self.console_utils.print_success("Dependencies installed successfully")
        
        # Pre-build step: Ensure we're in development mode for sandbox builds
        self.console_utils.print_step(1, 7, f"Ensuring {component} is in development mode for sandbox build...")
        self._ensure_component_development_mode(component)
        
        # Track results for summary
        results: List[Tuple[str, bool]] = []
        results.append(("Install Dependencies", True))  # Already succeeded if we got here
        
        # Step 2: Check lint
        self.console_utils.print_step(2, 7, "Checking component lint...")
        success = self._run_lint(verbose)
        results.append(("Lint Check", success))
        if not success:
            self.console_utils.print_error("Fix linting errors before continuing", exit_code=1)
        
        # Step 3: Test build
        self.console_utils.print_step(3, 7, "Testing component build...")
        success = self._run_test_build(verbose)
        results.append(("Test Build", success))
        if not success:
            self.console_utils.print_error("Fix build errors before continuing", exit_code=1)
        
        # Step 4: Bump version
        self.console_utils.print_step(4, 7, "Bumping alpha version...")
        current_version, new_version = self._bump_version(component, verbose)
        results.append(("Version Bump", bool(new_version)))
        
        if new_version:
            self.console_utils.print_success(f"Version: {current_version} → {new_version}")
        
        # Step 5: Build and publish
        self.console_utils.print_step(5, 7, "Publishing to CodeArtifact (@ai-sandbox)...")
        success, published_version = self._publish_component(component, verbose)
        results.append(("Publish", success))
        if not success:
            self.console_utils.print_error("Failed to publish component", exit_code=1)
        
        # Use the actual published version instead of the bumped version
        final_version = published_version if published_version else new_version
        
        # Step 6: Update application frontend package.json
        if final_version:
            self.console_utils.print_step(6, 7, f"Updating {app} frontend package.json...")
            success = self._update_frontend_package_json(component, final_version, app, verbose)
            results.append(("Frontend Update", success))
            if success:
                self.console_utils.print_success(f"Updated {app} frontend package.json with new component version")
                self.console_utils.print_info(
                    f"\nTo deploy the frontend with the new component:\n"
                    f"  cd ../{app}-frontend\n"
                    f"  docr deploy frontend"
                )
            else:
                self.console_utils.print_warning("Frontend package.json update failed")
        
        # Display summary
        self.display_results(results, f"{component.title()} Build Summary")
        
        # Check if publish was successful
        publish_success = any(name == "Publish" and success for name, success in results)
        
        if all(success for _, success in results) and publish_success and final_version:
            # Success message
            self.console_utils.print_success(
                f"\n✅ Published {component} v{final_version} to @ai-sandbox"
            )
    
    def _get_component_dir(self, component: str) -> Path:
        """Get the directory for a component."""
        from utils import AppConfig
        return AppConfig.get_component_frontend_dir(component)
    
    def _ensure_component_development_mode(self, component: str):
        """Ensure the specific component is in development mode for sandbox builds."""
        try:
            # Get component package.json path
            package_json = Path("package.json")
            if not package_json.exists():
                self.console_utils.print_warning("No package.json found in component directory")
                return
            
            # Read current package.json
            with open(package_json) as f:
                package_data = json.load(f)
            
            current_name = package_data.get("name", "")
            
            # Check if already in development mode
            if current_name.startswith("@ai-sandbox/"):
                self.console_utils.print_info(f"Component {component} already in development mode")
                return
            
            # Switch to development mode
            new_name = f"@ai-sandbox/{component}-component-react"
            package_data["name"] = new_name
            
            # Write updated package.json
            with open(package_json, "w") as f:
                json.dump(package_data, f, indent=2)
                f.write("\n")
            
            self.console_utils.print_success(f"Switched {component} to development mode (@ai-sandbox)")
            
        except Exception as e:
            self.console_utils.print_warning(f"Failed to switch component to development mode: {str(e)}")
            self.console_utils.print_info("Continuing with current registry state...")
    
    def _run_lint(self, verbose: bool) -> bool:
        """Run npm lint."""
        cmd = ["npm", "run", "lint"]
        if verbose:
            # Show full output
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
        else:
            # Always show lint output
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
    
    def _run_test_build(self, verbose: bool) -> bool:
        """Run test build."""
        cmd = ["npm", "run", "build"]
        if verbose:
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
        else:
            # Always show lint output
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
    
    def _bump_version(self, component: str, verbose: bool) -> Tuple[str, Optional[str]]:
        """Bump alpha version checking CodeArtifact first."""
        # Get current version and component info
        package_json = Path("package.json")
        with open(package_json) as f:
            package_data = json.load(f)
            current_version = package_data["version"]
            current_name = package_data["name"]
        
        # Get the actual target package name that will be used for publishing
        # This is important because the local package.json might have a different name
        from utils import AppConfig
        target_name = AppConfig.get_component_npm_package(component)
        
        if verbose:
            self.console_utils.print_info(f"Checking CodeArtifact for latest version of {target_name}")
        
        # Query CodeArtifact for latest version using the actual publish name
        latest_alpha = self._get_latest_codeartifact_version(target_name, verbose)
        
        if latest_alpha:
            # Extract alpha number and increment
            import re
            match = re.search(r'alpha\.(\d+)$', latest_alpha)
            if match:
                next_num = int(match.group(1)) + 1
                base_version = latest_alpha.split('-alpha')[0]
                new_version = f"{base_version}-alpha.{next_num}"
                
                # Update package.json
                package_data["version"] = new_version
                with open(package_json, "w") as f:
                    json.dump(package_data, f, indent=2)
                    f.write("\n")
                
                if verbose:
                    self.console_utils.print_info(f"Bumped to next available version: {new_version}")
                
                return current_version, new_version
        
        # Fallback to npm version if no versions found in CodeArtifact
        cmd = ["npm", "version", "prerelease", "--preid=alpha", "--no-git-tag-version"]
        result = subprocess.run(cmd, capture_output=False)
        
        if result.returncode != 0:
            self.console_utils.print_error("Failed to bump version!")
            return current_version, None
        
        # Get new version
        with open(package_json) as f:
            package_data = json.load(f)
            new_version = package_data["version"]
        
        return current_version, new_version
    
    def _get_latest_codeartifact_version(self, package_name: str, verbose: bool) -> Optional[str]:
        """Get latest alpha version from CodeArtifact."""
        # Use npm view to get all versions
        cmd = ["npm", "view", package_name, "versions", "--json"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            # Package doesn't exist yet in CodeArtifact
            if verbose:
                self.console_utils.print_info(f"Package {package_name} not found in CodeArtifact, will use npm version")
            return None
            
        if result.stdout:
            try:
                versions = json.loads(result.stdout)
                # Filter alpha versions and sort
                alpha_versions = [v for v in versions if '-alpha.' in v]
                if alpha_versions:
                    # Sort by alpha number
                    import re
                    def extract_alpha_num(v):
                        match = re.search(r'alpha\.(\d+)$', v)
                        return int(match.group(1)) if match else 0
                    
                    alpha_versions.sort(key=extract_alpha_num)
                    latest = alpha_versions[-1]
                    if verbose:
                        self.console_utils.print_info(f"Found latest version in CodeArtifact: {latest}")
                    return latest
            except Exception as e:
                self.console_utils.print_error(f"Failed to parse versions from CodeArtifact: {str(e)}")
                raise typer.Exit(1)
        
        return None
    
    def _publish_component(self, component_name: str, verbose: bool) -> Tuple[bool, Optional[str]]:
        """Build and publish to CodeArtifact. Returns (success, published_version)."""
        # Always use @ai-sandbox registry
        registry_config = self.REGISTRIES["@ai-sandbox"]
        
        # Step 1: Login to AWS CodeArtifact
        self.console.print("Logging in to AWS CodeArtifact (@ai-sandbox)...")
        login_cmd = [
            "aws", "codeartifact", "login",
            "--tool", "npm",
            "--repository", registry_config["repository"],
            "--domain", registry_config["domain"],
            "--domain-owner", registry_config["domain_owner"],
            "--region", "us-east-1"
        ]
        
        # Always show output for login
        login_result = subprocess.run(login_cmd, capture_output=False)
        if login_result.returncode != 0:
            self.console.print("\n[red]CodeArtifact login failed![/red]")
            return False, None
        
        # Save original package.json
        package_json = Path("package.json")
        with open(package_json) as f:
            original_package_data = json.load(f)
        
        published_version = None
        
        try:
            # Step 2: Get target package name from component metadata
            # We already know which component this is from the method parameter
            from utils import AppConfig
            target_package_name = AppConfig.get_component_npm_package(component_name)
            
            # Step 3: Update package.json for publishing
            publish_package_data = original_package_data.copy()
            publish_package_data["name"] = target_package_name
            publish_package_data["private"] = False
            
            # Store the version we're about to publish
            published_version = publish_package_data["version"]
            
            # Write updated package.json
            with open(package_json, "w") as f:
                json.dump(publish_package_data, f, indent=2)
                f.write("\n")
            
            # Step 4: Build
            if verbose:
                self.console.print("Building component...")
            
            # Show all build output
            build_result = subprocess.run(["npm", "run", "build"], capture_output=False)
            if build_result.returncode != 0:
                self.console.print("\n[red]Build failed![/red]")
                return False, None
            
            # Step 5: Publish
            if verbose:
                self.console.print(f"Publishing {target_package_name} to @ai-sandbox...")
            
            publish_cmd = ["npm", "publish", "--registry", registry_config["url"]]
            # Show all publish output - this is critical for debugging
            self.console.print(f"\n[cyan]Running: {' '.join(publish_cmd)}[/cyan]")
            publish_result = subprocess.run(publish_cmd, capture_output=False)
            
            if publish_result.returncode != 0:
                self.console.print("\n[red]CodeArtifact publish failed![/red]")
                return False, None
            
            return True, published_version
            
        finally:
            # Always restore original package.json
            with open(package_json, "w") as f:
                json.dump(original_package_data, f, indent=2)
                f.write("\n")
    
    def _display_verification(self, component: str, version: str, app_name: Optional[str], registry: str, verbose: bool):
        """Display verification table showing component status across CodeArtifact, component, and app."""
        from datetime import datetime
        
        # Get registry info
        registry_config = self.REGISTRIES[registry]
        package_name = self.package_names[component]
        
        # Query CodeArtifact for package info
        codeartifact_info = self._get_codeartifact_package_info(package_name, version, registry_config, verbose)
        
        # Read component package.json
        component_dir = self._get_component_dir(component)
        component_package_path = component_dir / "package.json"
        component_info = {"name": "Unknown", "version": "Unknown"}
        if component_package_path.exists():
            with open(component_package_path) as f:
                data = json.load(f)
                component_info = {
                    "name": data.get("name", "Unknown"),
                    "version": data.get("version", "Unknown")
                }
        
        # Read app package.json if specified
        app_info = None
        if app_name:
            try:
                from utils import AppConfig
                app_frontend_dir = AppConfig.get_app_frontend_dir(app_name)
                app_package_path = app_frontend_dir / "package.json"
                if app_package_path.exists():
                    with open(app_package_path) as f:
                        data = json.load(f)
                        deps = data.get("dependencies", {})
                        # Look for the component in dependencies
                        for dep_name, dep_value in deps.items():
                            if component in dep_name.lower():
                                app_info = {
                                    "name": dep_name,
                                    "value": dep_value
                                }
                                break
            except:
                pass
        
        # Create verification table
        self.console_utils.print_info("\n📋 Build Verification")
        
        table = Table(title=f"Component: {component.title()} v{version}", box=None)
        table.add_column("Location", style="cyan", width=25)
        table.add_column("Package Name", style="white", width=45)
        table.add_column("Version", style="green", width=20)
        table.add_column("Status", style="white", width=15)
        
        # CodeArtifact row
        if codeartifact_info:
            status = "✅ Published" if codeartifact_info["exists"] else "❌ Not Found"
            table.add_row(
                "CodeArtifact",
                package_name,
                version,
                status
            )
            if codeartifact_info["exists"] and codeartifact_info["published_time"]:
                table.add_row(
                    "  └─ Published",
                    "",
                    codeartifact_info["published_time"],
                    ""
                )
        
        # Component package.json row
        status = "✅ Match" if component_info["version"] == version else "⚠️ Mismatch"
        table.add_row(
            "Component package.json",
            component_info["name"],
            component_info["version"],
            status
        )
        
        # App package.json row (if applicable)
        if app_name and app_info:
            # Extract version from npm alias if present
            expected_value = f"npm:{package_name}@{version}"
            actual_value = app_info["value"]
            status = "✅ Match" if actual_value == expected_value else "⚠️ Mismatch"
            
            table.add_row(
                f"{app_name} package.json",
                app_info["name"],
                app_info["value"][:50] + "..." if len(app_info["value"]) > 50 else app_info["value"],
                status
            )
        
        self.console.print(table)
        
        # Print any warnings
        if component_info["version"] != version:
            self.console_utils.print_warning(
                f"\n⚠️  Component package.json shows v{component_info['version']} but published v{version}"
            )
    
    def _get_codeartifact_package_info(self, package_name: str, version: str, registry_config: Dict[str, str], verbose: bool = False) -> Optional[Dict[str, Any]]:
        """Query CodeArtifact for package information."""
        import subprocess
        from datetime import datetime
        
        # Remove @ from package name for namespace
        if package_name.startswith("@"):
            parts = package_name[1:].split("/")
            namespace = parts[0]
            package_short_name = parts[1]
        else:
            namespace = None
            package_short_name = package_name
        
        cmd = [
            "aws", "codeartifact", "describe-package-version",
            "--domain", registry_config["domain"],
            "--repository", registry_config["repository"],
            "--format", "npm",
            "--package", package_short_name,
            "--package-version", version
        ]
        
        if namespace:
            cmd.extend(["--namespace", namespace])
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                
                # Parse published time
                published_time = None
                if "publishedTime" in data.get("packageVersion", {}):
                    timestamp = data["packageVersion"]["publishedTime"]
                    # Just display the timestamp as-is if it's a string
                    if isinstance(timestamp, str):
                        published_time = timestamp.replace("T", " ").split(".")[0]  # Simple ISO format cleanup
                    else:
                        # Convert epoch to datetime
                        try:
                            dt = datetime.fromtimestamp(float(timestamp))
                            published_time = dt.strftime("%Y-%m-%d %H:%M:%S")
                        except:
                            published_time = str(timestamp)
                
                return {
                    "exists": True,
                    "published_time": published_time,
                    "status": data.get("packageVersion", {}).get("status", "Unknown")
                }
            else:
                return {"exists": False}
        except Exception as e:
            if verbose:
                self.console_utils.print_warning(f"Failed to query CodeArtifact: {str(e)}")
            return None
    
    def _update_frontend_package_json(self, component: str, new_version: str, app_name: str, verbose: bool) -> bool:
        """Update application frontend to use new component version."""
        # Get frontend directory for the app
        from utils import AppConfig
        try:
            frontend_dir = AppConfig.get_app_frontend_dir(app_name)
        except Exception as e:
            self.console_utils.print_error(f"Failed to get frontend directory for {app_name}: {e}")
            return False
        
        if not frontend_dir.exists():
            self.console_utils.print_error(f"Frontend directory not found: {frontend_dir}")
            return False
            
        # Save current directory to return to later
        original_dir = Path.cwd()
        
        try:
            os.chdir(frontend_dir)
            
            from utils import AppConfig
            package_name = AppConfig.get_component_npm_package(component)
            npm_alias = AppConfig.get_component_npm_alias(component)
            
            # Update package.json
            package_json = Path("package.json")
            with open(package_json) as f:
                package_data = json.load(f)
            
            # Find the actual package name in dependencies
            actual_package_name = None
            deps = package_data.get("dependencies", {})
            
            # Check direct match first
            if package_name in deps:
                actual_package_name = package_name
            # Check alias match
            elif npm_alias in deps:
                actual_package_name = npm_alias
            else:
                # Check for npm alias patterns in dependency values
                for dep_name, dep_value in deps.items():
                    if isinstance(dep_value, str) and dep_value.startswith("npm:"):
                        # Extract the actual package name from npm:package@version
                        npm_spec = dep_value[4:]  # Remove "npm:" prefix
                        if npm_spec.startswith(package_name + "@"):
                            actual_package_name = dep_name
                            break
            
            if actual_package_name:
                # Handle npm alias syntax
                if actual_package_name != package_name:
                    # Update with npm:package@version syntax
                    package_data["dependencies"][actual_package_name] = f"npm:{package_name}@{new_version}"
                else:
                    package_data["dependencies"][actual_package_name] = new_version
            else:
                self.console_utils.print_warning(
                    f"Package {package_name} not found in dependencies (also checked aliases and npm patterns)"
                )
                return False
            
            # Write updated package.json
            with open(package_json, "w") as f:
                json.dump(package_data, f, indent=2)
                f.write("\n")  # Add trailing newline
            
            # Just update package.json, don't install or build
            # The deploy command will handle that
            if verbose:
                self.console.print(f"Updated {app_name} package.json with {component} version {new_version}")
            
            return True
            
        finally:
            # Return to original directory
            os.chdir(original_dir)
    


def main():
    """Main entry point."""
    cli = FrontendBuildCLI()
    cli.run()


if __name__ == "__main__":
    main()