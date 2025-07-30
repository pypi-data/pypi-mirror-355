#!/usr/bin/env python3
"""
Frontend deployment CLI for legislative review.
Handles building and deploying the frontend to S3 and CloudFront.

This tool replaces the legacy deploy.sh script with a unified typer interface
that follows the same patterns as other CLI tools in the project.
"""
import os
import json
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import typer
from rich.table import Table
from dotenv import dotenv_values

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, CommandUtils, ConsoleUtils, AppConfig
from commands.refresh import refresh_config


class FrontendDeployCLI(BaseCLI):
    """Frontend deployment CLI."""
    
    # AWS configuration
    AWS_PROFILE = "default"
    AWS_REGION = "us-east-1"
    HOSTED_ZONE_ID = "Z02251061K965DXTYWXAK"
    
    def __init__(self):
        super().__init__(
            name="frontend-deploy",
            help_text="Deploy active application frontend to AWS.\n\n"
                     "Handles building the React application and deploying to S3/CloudFront.\n"
                     "Currently supports sandbox environment deployment only.",
            require_config=False,  # We handle our own config loading
            setup_python_path=False  # Don't require config for setup
        )
        
        # Get project root from config
        self.doc_review_root = AppConfig.get_project_root()
        
        # Frontend directory will be set when needed
        self.frontend_dir = None
        self.frontend_app = None
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        # Store self reference for closures
        cli = self
        
        @self.app.command()
        def deploy(
            app_name: str = typer.Option(..., "--app", help="Application to deploy (e.g., legislative-review)"),
            full: bool = typer.Option(False, "--full", "-f", 
                                        help="Include CloudFormation infrastructure updates (SAM deploy)"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", 
                                        help="Developer initials to use (overrides config)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", 
                                        help="Show detailed output"),
        ):
            """Deploy frontend to AWS S3 and CloudFront.
            
            This command:
            1. Loads environment configuration
            2. Builds the React application  
            3. Syncs build output to S3
            4. Creates CloudFront invalidation
            5. Optionally deploys infrastructure with SAM (when --full is used)
            
            Examples:
                S3-only deployment (default):
                    frontend-deploy deploy
                    
                Full deployment (includes CloudFormation):
                    frontend-deploy deploy --full
            """
            # When running frontend_deploy.py directly
            from utils import AppConfig
            
            # Set developer initials override if provided
            if developer_initials:
                try:
                    AppConfig.set_developer_initials_override(developer_initials)
                except ValueError as e:
                    cli.console_utils.print_error(f"Error: {str(e)}", exit_code=1)
            
            try:
                cli.run_deploy(app_name, not full, verbose)  # Note: inverting full to s3_only
            finally:
                # Clean up environment
                AppConfig.clear_developer_initials_override()
        
    
    def run_deploy(self, app_name: str, s3_only: bool, verbose: bool):
        """Run the deployment process for the specified application."""
        # Set the frontend directory and app name based on the provided app
        self.frontend_app = app_name
        self.frontend_dir = AppConfig.get_app_frontend_dir(app_name)
        
        # Validate that the frontend directory exists
        if not self.frontend_dir.exists():
            self.console_utils.print_error(
                f"Frontend directory not found for {app_name}: {self.frontend_dir}",
                exit_code=1
            )
        
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        try:
            refresh_config()
            self.console_utils.print_success("Configuration refreshed successfully!")
        except Exception as e:
            self.console_utils.print_warning(f"Failed to refresh config: {str(e)}")
            self.console_utils.print_info("Continuing with existing configuration...")
        
        self.console_utils.print_info(f"[DEBUG] Changing directory to: {self.frontend_dir}")
        os.chdir(self.frontend_dir)
        self.console_utils.print_info(f"[DEBUG] Current directory after chdir: {os.getcwd()}")
        
        # Validate required files first
        self.console_utils.print_info("[DEBUG] Validating required files...")
        if not self._validate_required_files(s3_only):
            self.console_utils.print_error("[DEBUG] Required files validation failed!")
            self.console_utils.print_error("Required files validation failed", exit_code=1)
        
        # Step 1: Validate environment configuration exists
        self.console_utils.print_step(1, 6, "Validating environment configuration exists...")
        config_valid = self._validate_config_exists()
        self.console_utils.print_info(f"[DEBUG] Config validation result: {config_valid}")
        if not config_valid:
            self.console_utils.print_error("[DEBUG] Exiting due to config validation failure")
            return  # Error already printed
        
        # Get developer initials from TOML config
        self.console_utils.print_info("[DEBUG] Getting developer initials...")
        dev_initials = AppConfig.get_developer_initials()
        dev_initials_lower = dev_initials.lower()
        self.console_utils.print_info(f"[DEBUG] Developer initials: {dev_initials}")
        
        # Get deployment configuration from TOML
        self.console_utils.print_info("[DEBUG] Loading TOML configuration...")
        config = AppConfig.load_config()
        self.console_utils.print_info(f"[DEBUG] Config loaded, contains {len(config)} top-level keys")
        app_config = None
        
        # Define appkey from app_name
        appkey = self.frontend_app
        
        # Find the app configuration based on the provided app name
        self.console_utils.print_info(f"[DEBUG] Looking for app config for: {self.frontend_app}")
        apps = config.get('applications', {})
        self.console_utils.print_info(f"[DEBUG] Available applications in config: {list(apps.keys())}")
        app_config = apps.get(self.frontend_app)
        self.console_utils.print_info(f"[DEBUG] Found app_config: {app_config is not None}")
        
        if not app_config:
            self.console_utils.print_error(f"[DEBUG] No app_config found!")
            self.console_utils.print_error(
                f"No configuration found for application: {self.frontend_app}",
                exit_code=1
            )
        
        # Get deployment configuration from TOML - no fallbacks
        frontend_stack_name = app_config.get('frontend_stack_name')
        if not frontend_stack_name:
            self.console_utils.print_error(
                f"No frontend_stack_name found in TOML configuration for {appkey}.\n"
                f"Run 'docr setup' to refresh configuration.",
                exit_code=1
            )
        
        # CloudFormation output validation - only required for S3-only deployments
        if s3_only:
            # For S3-only deployments, we need existing CloudFormation outputs
            frontend_url = app_config.get('stage_sandbox_frontend_url')
            if not frontend_url:
                self.console_utils.print_error(
                    f"No stage_sandbox_frontend_url found in TOML configuration for {appkey}.\n"
                    f"Make sure the frontend stack is deployed and run 'docr refresh' to refresh configuration.",
                    exit_code=1
                )
            
            bucket_name = app_config.get('frontend_bucket_name')
            if not bucket_name:
                self.console_utils.print_error(
                    f"No frontend_bucket_name found in TOML configuration for {appkey}.\n"
                    f"Make sure the frontend stack is deployed and run 'docr refresh' to refresh configuration.",
                    exit_code=1
                )
            
            cloudfront_distribution_id = app_config.get('cloudfront_distribution_id')
            if not cloudfront_distribution_id:
                self.console_utils.print_error(
                    f"No cloudfront_distribution_id found in TOML configuration for {appkey}.\n"
                    f"Make sure the frontend stack is deployed and run 'docr refresh' to refresh configuration.",
                    exit_code=1
                )
            
            # Extract subdomain from URL
            subdomain_prefix = frontend_url.replace('https://', '').split('.')[0]
        else:
            # For full deployments, generate expected values
            subdomain_prefix = f"{appkey}-{dev_initials_lower}"
            frontend_url = f"https://{subdomain_prefix}.it-eng-ai.aws.umd.edu"
            bucket_name = None  # Will be retrieved after CloudFormation deployment
            cloudfront_distribution_id = None  # Will be retrieved after CloudFormation deployment
        
        # Display deployment variables
        self.console_utils.print_info("Deployment variables:")
        deployment_vars = {
            "Frontend Stack Name": frontend_stack_name,
            "Subdomain Prefix": subdomain_prefix,
            "S3 Bucket Name": bucket_name or "(will be created)",
            "CloudFront Distribution": cloudfront_distribution_id or "(will be created)",
            "AWS Region": self.AWS_REGION,
            "Stage": "sandbox",
            "Deployment Mode": "S3 Only" if s3_only else "Full (CloudFormation + S3)"
        }
        
        table = self.console_utils.create_status_table("Deployment Configuration", deployment_vars)
        self.console.print(table)
        
        # Step 2: Configuration validation complete (already done in step 1)
        self.console_utils.print_step(2, 6, "Configuration validation complete...")
        
        # Step 3: Build application
        self.console_utils.print_step(3, 6, "Building React application for sandbox environment...")
        if not self._build_application(verbose):
            return
        
        # Step 4: Deploy infrastructure (unless s3-only)
        if not s3_only:
            self.console_utils.print_step(4, 6, "Deploying infrastructure with SAM...")
            if not self._deploy_infrastructure(frontend_stack_name, appkey, dev_initials_lower, 
                                             subdomain_prefix, verbose):
                return
        else:
            self.console_utils.print_step(4, 6, "Skipping CloudFormation updates (S3-only mode)...")
            if not self._verify_stack_exists(frontend_stack_name):
                return
        
        # Step 5: Get S3 bucket name (either from TOML or CloudFormation outputs)
        if s3_only:
            self.console_utils.print_step(5, 6, "Using S3 bucket name from configuration...")
            actual_bucket_name = bucket_name
        else:
            self.console_utils.print_step(5, 6, "Retrieving S3 bucket name from CloudFormation outputs...")
            actual_bucket_name = self._get_bucket_name(frontend_stack_name, "")
            if not actual_bucket_name:
                self.console_utils.print_error("Could not retrieve S3 bucket name from CloudFormation stack", exit_code=1)
                return
            
            # Also get CloudFront distribution ID for full deployments
            cloudfront_distribution_id = self._get_distribution_id(frontend_stack_name)
            if not cloudfront_distribution_id:
                self.console_utils.print_error("Could not retrieve CloudFront distribution ID from CloudFormation stack", exit_code=1)
                return
        
        self.console_utils.print_success(f"Bucket name: {actual_bucket_name}")
        
        if not actual_bucket_name:
            self.console_utils.print_error("Could not determine S3 bucket name", exit_code=1)
        
        # Step 6: Deploy to S3 and invalidate CloudFront
        self.console_utils.print_step(6, 6, f"Deploying frontend assets to S3 bucket: {actual_bucket_name}")
        distribution_id = self._deploy_to_s3(frontend_stack_name, actual_bucket_name, cloudfront_distribution_id, verbose)
        
        # Display completion message
        self._display_completion(frontend_stack_name, distribution_id)
    
    def _validate_required_files(self, s3_only: bool = False) -> bool:
        """Validate that required files exist before deployment."""
        self.console_utils.print_info(f"[DEBUG] _validate_required_files called with s3_only={s3_only}")
        self.console_utils.print_info(f"[DEBUG] Current frontend_dir: {self.frontend_dir}")
        
        required_files = ["package.json"]
        
        # samconfig.toml is only required for full deployment or S3-only mode
        # (S3-only mode needs it to get CloudFormation stack outputs)
        if not s3_only or s3_only:  # Always require samconfig.toml
            required_files.append("samconfig.toml")
        
        self.console_utils.print_info(f"[DEBUG] Required files to check: {required_files}")
        
        missing_files = []
        for file_name in required_files:
            file_path = self.frontend_dir / file_name
            exists = file_path.exists()
            self.console_utils.print_info(f"[DEBUG] Checking {file_name}: {'EXISTS' if exists else 'MISSING'} at {file_path}")
            if not exists:
                missing_files.append(file_name)
        
        if missing_files:
            self.console_utils.print_error(
                f"Missing required files: {', '.join(missing_files)}\n"
                f"Current directory: {self.frontend_dir}"
            )
            self.console_utils.print_error(f"[DEBUG] Validation failed - {len(missing_files)} files missing")
            return False
        
        self.console_utils.print_info("[DEBUG] All required files found - validation passed")
        return True
    
    def _validate_config_exists(self) -> bool:
        """Check that .env.production exists."""
        env_file = self.frontend_dir / ".env.production"
        self.console_utils.print_info(f"[DEBUG] Checking for .env.production at: {env_file}")
        self.console_utils.print_info(f"[DEBUG] File exists: {env_file.exists()}")
        
        if env_file.exists():
            self.console_utils.print_info(f"[DEBUG] File size: {env_file.stat().st_size} bytes")
            # Try to read first few lines
            try:
                with open(env_file, 'r') as f:
                    lines = f.readlines()[:5]
                self.console_utils.print_info(f"[DEBUG] First {len(lines)} lines of .env.production:")
                for i, line in enumerate(lines):
                    self.console_utils.print_info(f"[DEBUG]   Line {i+1}: {line.rstrip()}")
            except Exception as e:
                self.console_utils.print_error(f"[DEBUG] Error reading .env.production: {str(e)}")
        
        if not env_file.exists():
            # Use the already-detected app name from self.frontend_app
            app_name = self.frontend_app or "your-app"
            self.console_utils.print_error(
                f"Frontend configuration missing!\n\n"
                f"Required file not found: .env.production\n\n"
                f"Run this command to generate it:\n"
                f"  docr config frontend {app_name}\n\n"
                f"Then try deploying again.",
                exit_code=1
            )
            return False
        
        self.console_utils.print_info("[DEBUG] .env.production file exists - validation passed")
        return True
    
    
    def _build_application(self, verbose: bool) -> bool:
        """Build the React application."""
        
        # First run npm install to ensure dependencies are installed
        self.console_utils.print_info("Installing npm dependencies...")
        install_cmd = ["npm", "install"]
        
        if verbose:
            # Show full output
            install_result = subprocess.run(install_cmd, capture_output=False)
            if install_result.returncode != 0:
                self.console_utils.print_error("npm install failed")
                return False
        else:
            # Always show output for npm commands since they can take a while
            self.console_utils.print_info("Running: npm install")
            install_result = subprocess.run(install_cmd, capture_output=False)
            
            if install_result.returncode != 0:
                self.console_utils.print_error(f"npm install failed with exit code {install_result.returncode}")
                return False
            
            self.console_utils.print_success("Dependencies installed successfully!")
        
        # Now run the build
        cmd = ["npm", "run", "build", "--", "--mode", "production"]
        
        if verbose:
            # Show full output
            result = subprocess.run(cmd, capture_output=False)
            return result.returncode == 0
        else:
            # Always show output for npm build since it can take a while
            self.console_utils.print_info("Running: npm run build")
            result = subprocess.run(cmd, capture_output=False)
            
            if result.returncode != 0:
                self.console_utils.print_error(f"Build failed with exit code {result.returncode}")
                return False
            
            self.console_utils.print_success("Build completed successfully!")
            return True
    
    def _deploy_infrastructure(self, stack_name: str, appkey: str, 
                              dev_initials_lower: str, subdomain_prefix: str,
                              verbose: bool) -> bool:
        """Deploy infrastructure using SAM."""
        
        # Check if samconfig.toml exists
        samconfig_path = self.frontend_dir / "samconfig.toml"
        if not samconfig_path.exists():
            self.console_utils.print_error(
                f"samconfig.toml not found. Please create it from samconfig.toml.example"
            )
            return False
        
        cmd = [
            "sam", "deploy",
            "--capabilities", "CAPABILITY_IAM", "CAPABILITY_AUTO_EXPAND", "CAPABILITY_NAMED_IAM",
            "--stack-name", stack_name,
            "--resolve-s3",
            "--no-confirm-changeset",
            "--parameter-overrides",
            f"AppKey={appkey}",
            f"DeveloperInitialsLowercase={dev_initials_lower}",
            f"SubDomainPrefix={subdomain_prefix}",
            f"HostedZoneIdValue={self.HOSTED_ZONE_ID}"
        ]
        
        # Always show SAM output so users can see what's happening
        self.console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")
        result = subprocess.run(cmd, capture_output=False)
        success = result.returncode == 0
        
        if success:
            self.console_utils.print_success("SAM deployment completed successfully!")
        else:
            self.console_utils.print_error("SAM deployment failed")
        
        return success
    
    def _verify_stack_exists(self, stack_name: str) -> bool:
        """Verify CloudFormation stack exists."""
        
        success, _ = CommandUtils.run_aws_command(
            "cloudformation",
            "describe-stacks",
            ["--stack-name", stack_name],
            output="text"
        )
        
        if not success:
            self.console_utils.print_error(
                f"Stack {stack_name} not found. Please ensure you are logged in to AWS.\n"
                f"If you are logged in and this persists, please run a full deployment first."
            )
            return False
        
        return True
    
    def _get_bucket_name(self, stack_name: str, default_bucket: str) -> str:
        """Get S3 bucket name from CloudFormation outputs."""
        
        # Try to get bucket name from stack outputs
        success, output = CommandUtils.run_aws_command(
            "cloudformation",
            "describe-stacks",
            ["--stack-name", stack_name],
            query="Stacks[0].Outputs[?OutputKey=='FrontendBucketName'].OutputValue",
            output="text"
        )
        
        if success and output and output != "None":
            bucket_name = output
            self.console_utils.print_success(f"Found bucket name in CloudFormation outputs: {bucket_name}")
        else:
            self.console_utils.print_warning(
                f"Cannot find FrontendBucketName in stack outputs, using default: {default_bucket}"
            )
            bucket_name = default_bucket
        
        return bucket_name
    
    def _deploy_to_s3(self, stack_name: str, bucket_name: str, distribution_id: str,
                     verbose: bool) -> Optional[str]:
        """Deploy to S3 and invalidate CloudFront."""
        # Check if dist directory exists
        dist_dir = self.frontend_dir / "dist"
        if not dist_dir.exists():
            self.console_utils.print_error(
                "Build directory 'dist' not found. Please run build first."
            )
            return None
        
        
        # Sync to S3
        self.console_utils.print_info(f"Syncing files to S3 bucket: {bucket_name}")
        
        sync_cmd = [
            "aws", "s3", "sync",
            str(dist_dir),  # AWS S3 sync handles directories properly without trailing slash
            f"s3://{bucket_name}",
            "--delete",
            "--profile", self.AWS_PROFILE,
            "--region", self.AWS_REGION
        ]
        
        if verbose:
            sync_result = subprocess.run(sync_cmd, capture_output=False)
            success = sync_result.returncode == 0
        else:
            with self.console_utils.get_progress("Syncing to S3...") as progress:
                task = progress.add_task("Uploading...", total=None)
                success, output = CommandUtils.run_command(sync_cmd, shell=False, check=False)
                progress.update(task, completed=True)
        
        if not success:
            self.console_utils.print_error("Failed to sync to S3")
            return None
        
        self.console_utils.print_success("Files synced to S3 successfully!")
        
        # Get CloudFront distribution ID
        # Use the distribution ID passed from configuration
        if distribution_id:
            # Create invalidation
            self.console_utils.print_info(
                f"Creating CloudFront invalidation for distribution: {distribution_id}"
            )
            
            invalidate_cmd = [
                "aws", "cloudfront", "create-invalidation",
                "--distribution-id", distribution_id,
                "--paths", "/*",
                "--profile", self.AWS_PROFILE,
                "--region", self.AWS_REGION,
                "--no-cli-pager"
            ]
            
            success, _ = CommandUtils.run_command(invalidate_cmd, shell=False, check=False)
            
            if success:
                self.console_utils.print_success("CloudFront invalidation created!")
            else:
                self.console_utils.print_warning("Failed to create CloudFront invalidation")
        
        return distribution_id
    
    def _get_distribution_id(self, stack_name: str) -> Optional[str]:
        """Get CloudFront distribution ID from stack outputs."""
        # Try main stack first
        success, output = CommandUtils.run_aws_command(
            "cloudformation",
            "describe-stacks",
            ["--stack-name", stack_name],
            query="Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue",
            output="text"
        )
        
        if success and output and output != "None":
            return output
        
        # Try nested stack
        nested_stack_name = f"{stack_name}-FrontendResources"
        success, output = CommandUtils.run_aws_command(
            "cloudformation",
            "describe-stacks",
            ["--stack-name", nested_stack_name],
            query="Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue",
            output="text"
        )
        
        if success and output and output != "None":
            self.console_utils.print_info("Found CloudFront distribution ID in nested stack")
            return output
        
        self.console_utils.print_warning("CloudFront distribution ID not found in stack outputs")
        return None
    
    def _display_completion(self, stack_name: str, distribution_id: Optional[str]):
        """Display deployment completion message."""
        
        self.console_utils.print_success("Deployment complete!")
        
        if distribution_id:
            # Get CloudFront domain
            success, cf_domain = CommandUtils.run_aws_command(
                "cloudfront",
                "list-distributions",
                query=f"DistributionList.Items[?Id=='{distribution_id}'].DomainName",
                output="text"
            )
            
            if success and cf_domain:
                self.console_utils.print_info(
                    f"Your application will be available at: https://{cf_domain}"
                )
            
            # Get custom domain
            for stack in [stack_name, f"{stack_name}-FrontendResources"]:
                success, custom_domain = CommandUtils.run_aws_command(
                    "cloudformation",
                    "describe-stacks",
                    ["--stack-name", stack],
                    query="Stacks[0].Outputs[?OutputKey=='CustomDomainName'].OutputValue",
                    output="text"
                )
                
                if success and custom_domain and custom_domain != "None":
                    self.console_utils.print_info(
                        f"Your application will also be available at: https://{custom_domain}"
                    )
                    
                    # Check for duplicated developer initials
                    dev_initials_lower = stack_name.split('-')[-1]
                    if f"{dev_initials_lower}-{dev_initials_lower}" in custom_domain:
                        self.console_utils.print_warning(
                            "Custom domain appears to have duplicated developer initials.\n"
                            "This indicates a mismatch between deployment configuration.\n"
                            "Please check your configuration files."
                        )
                    break
        else:
            self.console_utils.print_info("Deployment to S3 complete!")


def main():
    """Main entry point."""
    cli = FrontendDeployCLI()
    cli.run()


if __name__ == "__main__":
    main()