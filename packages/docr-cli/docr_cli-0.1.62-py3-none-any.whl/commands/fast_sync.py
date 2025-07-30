#!/usr/bin/env python3
"""
Universal Fast Sync CLI for rapid Lambda deployment using ECR.
Deploys the specified application or component backend.

Works with:
- legislative-review-backend
- workspaces-component-backend  
- cost-component-backend
- jobs-component-backend
- oidc-manager-backend
- oidc-oidcauthorizer-serverless

Usage:
    cd /path/to/any-backend-module
    python /path/to/fast-sync.py sync
"""
import platform
import time
from pathlib import Path
from typing import Optional, Dict, Tuple
import typer
import boto3
from botocore.exceptions import ClientError
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, ConfigUtils, ConsoleUtils, CommandUtils, SystemUtils, AWSUtils
from commands.refresh import refresh_config


# Module detection now uses TOML config as single source of truth


class UniversalPathUtils:
    """Path utilities for fast sync deployment."""
    
    @staticmethod
    def get_stack_name(backend_root: Path) -> Optional[str]:
        """Extract stack name from samconfig.toml."""
        samconfig_path = backend_root / "samconfig.toml"
        try:
            # Try using toml if available
            import toml
            config = toml.load(samconfig_path)
            return config.get('default', {}).get('deploy', {}).get('parameters', {}).get('stack_name')
        except ImportError:
            # Fallback to regex parsing
            try:
                with open(samconfig_path, 'r') as f:
                    content = f.read()
                    import re
                    match = re.search(r'stack_name\s*=\s*["\'](.*?)["\']', content)
                    if match:
                        return match.group(1)
            except Exception:
                pass
        return None


class FastSyncCLI(BaseCLI):
    """Fast sync Lambda deployment CLI."""
    
    def __init__(self):
        super().__init__(
            name="fast-sync",
            help_text="Universal fast sync Lambda deployment via ECR",
            require_config=False,  # We handle config differently
            setup_python_path=False  # Not needed for this tool
        )
        self.command_utils = CommandUtils()
        
    def get_architecture(self) -> str:
        """Detect system architecture."""
        machine = platform.machine().lower()
        if machine in ['arm64', 'aarch64']:
            return 'arm64'
        return 'x86_64'
    
    def get_stack_outputs(self, stack_name: str) -> Dict[str, str]:
        """Get CloudFormation stack outputs."""
        from utils.cloudformation_utils import get_stack_outputs as get_outputs
        return get_outputs(stack_name, fail_on_error=True, console_utils=self.console_utils)
    
    
    def ensure_shared_ecr_repo(self, repo_name: str = None) -> str:
        """Ensure the shared ECR repository exists, create if not."""
        if repo_name is None:
            from utils import AppConfig
            dev_initials = AppConfig.get_developer_initials()
            repo_name = f"fastsync-{dev_initials}"
        
        ecr_client = boto3.client('ecr', region_name='us-east-1')
        
        try:
            # Check if repository exists
            response = ecr_client.describe_repositories(repositoryNames=[repo_name])
            ConsoleUtils.success(f"ECR repository '{repo_name}' already exists")
            return response['repositories'][0]['repositoryUri']
        except ClientError as e:
            if e.response['Error']['Code'] == 'RepositoryNotFoundException':
                # Create repository
                self.console.print(f"[yellow]Creating ECR repository '{repo_name}'...[/yellow]")
                try:
                    response = ecr_client.create_repository(
                        repositoryName=repo_name,
                        imageScanningConfiguration={'scanOnPush': True},
                        imageTagMutability='MUTABLE'
                    )
                    ConsoleUtils.success(f"Created ECR repository '{repo_name}'")
                    return response['repository']['repositoryUri']
                except ClientError as create_error:
                    if create_error.response['Error']['Code'] == 'RepositoryAlreadyExistsException':
                        # Handle race condition where repo was created between check and create
                        response = ecr_client.describe_repositories(repositoryNames=[repo_name])
                        return response['repositories'][0]['repositoryUri']
                    raise
            raise
    
    def get_shared_ecr_repo(self) -> Tuple[str, str]:
        """Get shared ECR repository name and URI."""
        # Ensure repo exists and get URI
        repo_uri = self.ensure_shared_ecr_repo()
        
        # Extract repository name from URI
        if '.amazonaws.com/' in repo_uri:
            repo_name = repo_uri.split('.amazonaws.com/')[-1]
        else:
            repo_name = repo_uri
        
        return repo_name, repo_uri
    
    def check_poetry_lock(self) -> None:
        """Check if poetry.lock is in sync with pyproject.toml."""
        # Skip poetry check if we don't have pyproject.toml (not a Python project)
        if not Path("pyproject.toml").exists():
            if Path("package.json").exists():
                self.console.print("[dim]Node.js project detected, skipping poetry check[/dim]")
            else:
                self.console.print("[dim]No pyproject.toml found, skipping poetry check[/dim]")
            return
            
        success, _ = self.command_utils.run_command(['poetry', '--version'], capture_output=True)
        if not success:
            ConsoleUtils.warning("Poetry not found. Skipping lock file check.")
            return
        
        self.console.print("[blue]Checking poetry.lock file...[/blue]")
        success, _ = self.command_utils.run_command(['poetry', 'check', '--lock'], capture_output=True)
        
        if not success:
            ConsoleUtils.warning("poetry.lock is out of sync with pyproject.toml. Updating...")
            success, _ = self.command_utils.run_command(['poetry', 'lock'])
            if success:
                ConsoleUtils.success("poetry.lock updated successfully")
            else:
                self.console_utils.print_error("Failed to update poetry.lock", exit_code=1)
        else:
            ConsoleUtils.success("poetry.lock is up to date")
    
    def check_poetry_lock_in_dir(self, directory: Path) -> None:
        """Check if poetry.lock is in sync with pyproject.toml in a specific directory."""
        # Skip poetry check if we don't have pyproject.toml (not a Python project)
        pyproject_path = directory / "pyproject.toml"
        package_json_path = directory / "package.json"
        
        if not pyproject_path.exists():
            if package_json_path.exists():
                self.console.print("[dim]Node.js project detected, skipping poetry check[/dim]")
            else:
                self.console.print("[dim]No pyproject.toml found, skipping poetry check[/dim]")
            return
            
        success, _ = self.command_utils.run_command(['poetry', '--version'], capture_output=True)
        if not success:
            ConsoleUtils.warning("Poetry not found. Skipping lock file check.")
            return
        
        self.console.print("[blue]Checking poetry.lock file...[/blue]")
        success, _ = self.command_utils.run_command(['poetry', 'check', '--lock'], capture_output=True, cwd=directory)
        
        if not success:
            ConsoleUtils.warning("poetry.lock is out of sync with pyproject.toml. Updating...")
            success, _ = self.command_utils.run_command(['poetry', 'lock'], cwd=directory)
            if success:
                ConsoleUtils.success("poetry.lock updated successfully")
            else:
                self.console_utils.print_error("Failed to update poetry.lock", exit_code=1)
        else:
            ConsoleUtils.success("poetry.lock is up to date")
    
    def get_lambda_architecture(self, function_name: str) -> str:
        """Get the architecture of the Lambda function."""
        cmd = [
            'aws', 'lambda', 'get-function',
            '--no-cli-pager', '--function-name', function_name,
            '--query', 'Configuration.Architectures[0]',
            '--output', 'text'
        ]
        
        success, output = self.command_utils.run_command(cmd, capture_output=True)
        if not success:
            self.console_utils.print_error(f"Failed to get Lambda architecture: {output}", exit_code=1)
        
        return output.strip()


# Create CLI instance
cli = FastSyncCLI()
app = cli.app


@app.callback(invoke_without_command=True)
def main_sync(
    ctx: typer.Context,
    app_name: str = typer.Option(..., "--app", help="Application or component to deploy (required)"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
):
    """Build and deploy Lambda function using fast ECR sync."""
    # If a subcommand was invoked, don't run sync
    if ctx.invoked_subcommand is not None:
        return
    
    # Run the sync functionality
    run_sync_deployment(app_name, developer_initials)


@app.command()
def sync(
    app_name: str = typer.Option(..., "--app", help="Application or component to deploy (required)"),
    developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
):
    """Build and deploy Lambda function using fast ECR sync."""
    run_sync_deployment(app_name, developer_initials)


def run_sync_deployment(module: str, developer_initials: Optional[str] = None):
    """Build and deploy Lambda function using fast ECR sync."""
    # Refresh configuration first to ensure we have latest stack outputs
    cli.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
    refresh_config()
    
    from utils import AppConfig
    
    # Override developer initials if provided
    if developer_initials:
        AppConfig.set_developer_initials_override(developer_initials)
    
    # Check prerequisites (Docker and AWS)
    ConsoleUtils.info("Checking Prerequisites...")
    
    # Check AWS credentials
    aws_valid, aws_msg = AWSUtils.verify_aws_token()
    if aws_valid:
        ConsoleUtils.success(aws_msg)
    else:
        cli.console_utils.print_error(aws_msg, exit_code=1)
        raise typer.Exit(1)
    
    # Check Docker
    docker_valid, docker_msg = SystemUtils.verify_docker()
    if docker_valid:
        ConsoleUtils.success(docker_msg)
    else:
        cli.console_utils.print_error(docker_msg, exit_code=1)
    if not docker_valid:
        raise typer.Exit(1)
    
    ConsoleUtils.success("Prerequisites check passed")
    
    # Validate module and get backend directory using TOML config
    available_modules = AppConfig.discover_applications() + AppConfig.discover_components()
    
    # Handle oidc-authorizer special case - check if it exists in OIDC config
    oidc_config = AppConfig.load_config().get('oidc', {})
    if 'authorizer' in oidc_config:
        available_modules.append('oidc-authorizer')
    
    if module not in available_modules:
        cli.console_utils.print_error(
            f"Invalid module: {module}\n"
            f"Valid modules: {', '.join(available_modules)}",
            exit_code=1
        )
    
    # Get backend directory path using AppConfig
    if AppConfig.is_application(module):
        backend_root = AppConfig.get_app_backend_dir(module)
    elif AppConfig.is_component(module):
        backend_root = AppConfig.get_component_backend_dir(module)
    elif module == 'oidc-authorizer':
        # Get oidc-authorizer path from OIDC config
        backend_root = AppConfig.get_oidc_directory_path('authorizer')
    else:
        cli.console_utils.print_error(f"Unknown module type: {module}", exit_code=1)
        raise typer.Exit(1)
    
    # Verify the backend directory exists and has required files
    try:
        AppConfig.validate_directory_exists(backend_root, f"backend directory for {module}")
        
        # Check for required files
        if not (backend_root / "samconfig.toml").exists() and not (backend_root / "template.yaml").exists():
            cli.console_utils.print_error(
                f"Backend directory exists but missing samconfig.toml or template.yaml: {backend_root}",
                exit_code=1
            )
            raise typer.Exit(1)
    except (FileNotFoundError, NotADirectoryError) as e:
        cli.console_utils.print_error(str(e), exit_code=1)
        raise typer.Exit(1)
    
    ConsoleUtils.success(f"Module: {module}")
    ConsoleUtils.success(f"Backend directory: {backend_root}")
    
    # Always check and update poetry lock if needed (in the backend directory)
    cli.check_poetry_lock_in_dir(backend_root)
    
    # For Node.js projects (oidc-authorizer), remove package-lock.json to fix auth issues
    if module == 'oidc-authorizer' and (backend_root / "package.json").exists():
        # Delete package-lock.json to fix CodeArtifact authentication issues
        # When using AWS CodeArtifact, package-lock.json can contain outdated auth tokens
        # that cause npm install to fail with 401 errors during Docker builds.
        # Removing it forces npm to use current authentication from ~/.npmrc
        package_lock = backend_root / "package-lock.json"
        if package_lock.exists():
            cli.console.print("[blue]Removing package-lock.json to fix CodeArtifact authentication...[/blue]")
            try:
                package_lock.unlink()
                ConsoleUtils.success("package-lock.json removed successfully")
            except Exception as e:
                ConsoleUtils.warning(f"Could not remove package-lock.json: {e}")
    
    # Get stack name from samconfig.toml
    stack_name = UniversalPathUtils.get_stack_name(backend_root)
    if not stack_name:
        cli.console_utils.print_error(
            "Stack name not found in samconfig.toml\n"
            "Please ensure samconfig.toml contains stack_name parameter.",
            exit_code=1
        )
    
    cli.console.print(f"[blue]Using stack: {stack_name}[/blue]")
    
    # Get stack outputs
    cli.console.print(f"[blue]Fetching configuration from CloudFormation stack...[/blue]")
    outputs = cli.get_stack_outputs(stack_name)
    
    # Different output keys for different modules
    if module == 'oidc-authorizer':
        lambda_function_name = outputs.get('OidcLambdaAuthorizerFunctionName')
    else:
        lambda_function_name = outputs.get('FastSyncLambdaName')
    
    if not lambda_function_name:
        expected_key = 'OidcLambdaAuthorizerFunctionName' if module == 'oidc-authorizer' else 'FastSyncLambdaName'
        cli.console_utils.print_error(
            f"Could not fetch Lambda function name from stack outputs (expected key: {expected_key})\n"
            f"Available outputs: {list(outputs.keys())}",
            exit_code=1
        )
    
    ConsoleUtils.success(f"Using Lambda function: {lambda_function_name}")
    
    # Detect architecture
    local_arch = cli.get_architecture()
    cli.console.print(f"[blue]Detected local architecture: {local_arch}[/blue]")
    
    # Check Lambda architecture
    lambda_arch = cli.get_lambda_architecture(lambda_function_name)
    cli.console.print(f"[blue]Lambda function architecture: {lambda_arch}[/blue]")
    
    # Architecture compatibility check - just warn, don't prompt
    if local_arch != lambda_arch:
        ConsoleUtils.warning(
            f"Architecture mismatch: Local {local_arch} vs Lambda {lambda_arch}\n"
            f"Proceeding with deployment anyway..."
        )
    
    # Get developer initials from config (needed for ECR repo names)
    # Get developer initials from TOML config
    from utils import AppConfig
    dev_initials = AppConfig.get_developer_initials()
    
    # ECR registry constant
    ecr_registry = "265858620073.dkr.ecr.us-east-1.amazonaws.com"
    
    # Create or use the shared ECR repository
    repo_name, ecr_uri = cli.get_shared_ecr_repo()
    ConsoleUtils.success(f"Using shared ECR repository: {repo_name}")
    
    # Different image tags for different modules
    if module == 'oidc-authorizer':
        image_tag = f"oidclambdaauthorizerfunction-nodejs22-{local_arch}-v1"
        docker_tag_param = f'DockerTag=nodejs22-{local_arch}-v1'
    else:
        image_tag = f"backendfunction-python3.11-{local_arch}-v1"
        docker_tag_param = f'DockerTag=python3.11-{local_arch}-v1'
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=cli.console,
    ) as progress:
        # ECR login
        task = progress.add_task("[blue]Authenticating with ECR...", total=None)
        login_cmd = f'aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {ecr_registry}'
        success, output = cli.command_utils.run_shell_command(login_cmd)
        if not success:
            cli.console_utils.print_error(f"Failed to login to ECR: {output}", exit_code=1)
            raise typer.Exit(1)
        progress.update(task, completed=True)
        
        # SAM build
        task = progress.add_task(f"[blue]Building for {local_arch} architecture...", total=None)
        build_cmd = ['sam', 'build', '--use-container', '--parameter-overrides', docker_tag_param]
        success, _ = cli.command_utils.run_command(build_cmd, cwd=backend_root)
        if not success:
            cli.console_utils.print_error("SAM build failed", exit_code=1)
            raise typer.Exit(1)
        progress.update(task, completed=True)
        
        # Tag image with module name prefix
        timestamp = time.strftime('%Y%m%d%H%M%S')
        full_image_tag = f"{module}-{image_tag}-{timestamp}"
        
        task = progress.add_task("[blue]Tagging Docker image...", total=None)
        # Different source image names for different modules
        if module == 'oidc-authorizer':
            source_image = f'oidclambdaauthorizerfunction:nodejs22-{local_arch}-v1'
        else:
            source_image = f'backendfunction:python3.11-{local_arch}-v1'
            
        tag_cmd = [
            'docker', 'tag',
            source_image,
            f'{ecr_uri}:{full_image_tag}'
        ]
        success, _ = cli.command_utils.run_command(tag_cmd)
        if not success:
            cli.console_utils.print_error("Failed to tag Docker image", exit_code=1)
            raise typer.Exit(1)
        progress.update(task, completed=True)
        
        # Push image
        task = progress.add_task("[blue]Pushing Docker image to ECR...", total=None)
        push_cmd = ['docker', 'push', f'{ecr_uri}:{full_image_tag}']
        success, _ = cli.command_utils.run_command(push_cmd)
        if not success:
            cli.console_utils.print_error("Failed to push Docker image", exit_code=1)
            raise typer.Exit(1)
        progress.update(task, completed=True)
        
        # Update Lambda
        task = progress.add_task("[blue]Updating Lambda function...", total=None)
        update_cmd = [
            'aws', 'lambda', 'update-function-code',
            '--no-cli-pager',
            '--function-name', lambda_function_name,
            '--image-uri', f'{ecr_uri}:{full_image_tag}'
        ]
        success, _ = cli.command_utils.run_command(update_cmd)
        if not success:
            cli.console_utils.print_error("Failed to update Lambda function", exit_code=1)
            raise typer.Exit(1)
        progress.update(task, completed=True)
        
        # Wait for Lambda to be active
        task = progress.add_task("[blue]Waiting for Lambda to be active...", total=None)
        max_attempts = 60  # Max 60 seconds
        attempt = 0
        
        while attempt < max_attempts:
            # Check Lambda state
            state_cmd = [
                'aws', 'lambda', 'get-function',
                '--no-cli-pager',
                '--function-name', lambda_function_name,
                '--query', 'Configuration.State',
                '--output', 'text'
            ]
            success, state = cli.command_utils.run_command(state_cmd, capture_output=True)
            
            if success and state.strip() == 'Active':
                # Also check LastUpdateStatus to ensure it's successful
                update_status_cmd = [
                    'aws', 'lambda', 'get-function',
                    '--no-cli-pager',
                    '--function-name', lambda_function_name,
                    '--query', 'Configuration.LastUpdateStatus',
                    '--output', 'text'
                ]
                success, update_status = cli.command_utils.run_command(update_status_cmd, capture_output=True)
                
                if success and update_status.strip() == 'Successful':
                    progress.update(task, completed=True)
                    break
                elif success and update_status.strip() == 'Failed':
                    progress.update(task, completed=True)
                    cli.console_utils.print_error("Lambda update failed!", exit_code=1)
                    raise typer.Exit(1)
            
            attempt += 1
            time.sleep(1)  # Wait 1 second before next check
            
        if attempt >= max_attempts:
            progress.update(task, completed=True)
            ConsoleUtils.warning("Lambda update is taking longer than expected. Check AWS Console for status.")
    
    ConsoleUtils.success("Lambda function is active and ready!")
    cli.console.print(f"[dim]Image: {ecr_uri}:{full_image_tag}[/dim]")




if __name__ == "__main__":
    app()