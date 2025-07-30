#!/usr/bin/env python3
"""
Unified job runner CLI for triggering monitor and sync jobs.
Clean implementation using Typer for better CLI experience.
"""
from pathlib import Path
from typing import Optional
import typer

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, ConfigUtils, DirectInvokeClient
from commands.refresh import refresh_config


class JobsCLI(BaseCLI):
    """CLI for running legislative review jobs."""
    
    def __init__(self):
        super().__init__(
            name="jobs",
            help_text="Run legislative review jobs",
            require_config=True
        )
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.command()
        def monitor(
            app: str = typer.Option(..., "--app", help="Application name (required)"),
            org_id: str = typer.Option("umd-org", "--org", "-o", help="Organization ID"),
            ws_id: str = typer.Option("umd-ogc-state-ws", "--workspace", "-w", help="Workspace ID"),
            user_id: str = typer.Option("manual-trigger", "--user", "-u", help="User ID"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
        ):
            """Trigger a monitor bills job."""
            self.run_monitor(app, org_id, ws_id, user_id, developer_initials, verbose)
        
        @self.app.command()
        def sync(
            app: str = typer.Option(..., "--app", help="Application name (required)"),
            session: str = typer.Option("2025RS", "--session", help="Legislative session (e.g., 2025RS, 2024RS)"),
            user_id: str = typer.Option("manual-trigger", "--user", "-u", help="User ID"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
            verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
        ):
            """Trigger a sync Maryland bills job."""
            self.run_sync(session, app, user_id, developer_initials, verbose)
        
        @self.app.command()
        def list():
            """List available job types."""
            self.list_jobs()
        
        @self.app.command()
        def status(
            job_id: str = typer.Argument(..., help="Job ID to check status for"),
            developer_initials: Optional[str] = typer.Option(None, "--developer-initials", "-d", help="Developer initials to use (overrides config)"),
        ):
            """Check the status of a job."""
            self.check_status(job_id, developer_initials)
    
    def setup_environment(self, config: ConfigUtils, app_name: str):
        """Set up environment for job execution."""
        try:
            # Jobs module needs minimal environment variables:
            # 1. Credential store vars (for authentication)
            # 2. SNS_TOPIC_ARN is set separately below
            # 3. JOBS_LAMBDA_FUNCTION_NAME is set by DirectInvokeClient
            
            # Only set credential store environment variables
            # No need to set all config variables
            config.setup_environment(include_credential_store=True, env_filter=[])
            
            # Get SNS topic ARN from TOML config
            from utils import AppConfig
            
            # Add the app's backend directory to Python path for imports
            backend_dir = AppConfig.get_app_backend_dir(app_name)
            if backend_dir.exists():
                import sys
                backend_dir_str = str(backend_dir)
                if backend_dir_str not in sys.path:
                    sys.path.insert(0, backend_dir_str)
            else:
                self.console_utils.print_error(
                    f"Backend directory not found for {app_name}: {backend_dir}\n"
                    "Please ensure the application exists in your project structure.",
                    exit_code=1
                )
            
            sns_topic_arn = AppConfig.get_sns_topic_arn(app_name)
            
            if not sns_topic_arn:
                self.console_utils.print_error(
                    f"SNS topic ARN not found for {app_name} in configuration.\n"
                    "Run 'docr refresh' to update configuration from AWS CloudFormation outputs.\n"
                    f"The SNS topic ARN should be available in the {app_name} stack outputs.",
                    exit_code=1
                )
            
            # Set as environment variable for SNSManager
            import os
            os.environ['SNS_TOPIC_ARN'] = sns_topic_arn
        except ValueError as e:
            self.console_utils.print_error(
                f"Configuration error: {str(e)}\n"
                "Please check your configuration and try again.",
                exit_code=1
            )
        except Exception as e:
            self.console_utils.print_error(
                f"Failed to setup environment: {str(e)}\n"
                "Please check your configuration and try again.",
                exit_code=1
            )
    
    def run_monitor(self, app: str, org_id: str, ws_id: str, user_id: str, developer_initials: Optional[str], verbose: bool):
        """Trigger a monitor bills job."""
        # Set developer initials override if provided
        if developer_initials:
            from utils import AppConfig
            AppConfig.set_developer_initials_override(developer_initials)
        
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        if verbose:
            self.setup_logging("DEBUG")
        
        # Load config and setup environment
        config = self.load_config(app_name=app)  # Always use sandbox
        self.setup_environment(config, app_name=app)
        
        # Set up JOBS_LAMBDA_FUNCTION_NAME environment variable
        direct_invoke_client = DirectInvokeClient("jobs")
        import os
        os.environ['JOBS_LAMBDA_FUNCTION_NAME'] = direct_invoke_client.function_name
        
        # Import here after environment is set up
        from app.clients.job_client import JobClient
        from app.jobs.core.sns_manager import SNSManager
        
        try:
            # Create clients
            job_client = JobClient()
            sns_manager = SNSManager()
            
            with self.console_utils.get_progress("Creating monitor job...") as progress:
                task = progress.add_task("Processing...", total=None)
                
                # Create the job in the Jobs service
                job_record = job_client.create_workspace_job(
                    process_name='monitor_bills',
                    org_id=org_id,
                    ws_id=ws_id,
                    user_id=user_id
                )
                
                # Publish to SNS to trigger execution
                sns_manager.publish_message(
                    job_type="monitor_bills",
                    job_id=job_record.job_id,
                    params={
                        "org_id": org_id,
                        "ws_id": ws_id
                    },
                    user_id=user_id
                )
                
                progress.update(task, completed=True)
            
            self.console_utils.print_success("Monitor job created successfully!")
            
            # Display job details
            job_data = {
                "Job ID": job_record.job_id,
                "Process": "monitor_bills",
                "Organization": org_id,
                "Workspace": ws_id,
                "User": user_id,
                "Status": job_record.status
            }
            
            table = self.console_utils.create_status_table("Job Details", job_data)
            self.console.print(table)
            
            self.console.print(f"\n[bold yellow]Job ID: {job_record.job_id}[/bold yellow]")
            self.console.print(f"\n[blue]To check status, run:[/blue]")
            self.console.print(f"[cyan]./jobs.py status {job_record.job_id}[/cyan]")
            self.console.print("\n[blue]Check CloudWatch logs for detailed progress[/blue]")
            
        except Exception as e:
            self.console_utils.print_error(f"Failed to create monitor job: {str(e)}")
            if verbose:
                self.handle_error(e, debug=True)
            raise typer.Exit(1)
    
    def run_sync(self, session: str, app: str, user_id: str, developer_initials: Optional[str], verbose: bool):
        """Trigger a sync Maryland bills job."""
        # Set developer initials override if provided
        if developer_initials:
            from utils import AppConfig
            AppConfig.set_developer_initials_override(developer_initials)
        
        # Refresh configuration first to ensure we have latest stack outputs
        self.console_utils.print_info("Refreshing configuration from AWS CloudFormation...")
        refresh_config()
        
        if verbose:
            self.setup_logging("DEBUG")
        
        # App is now required, so we can use it directly
        appkey = app
        
        # Load config and setup environment
        config = self.load_config(app_name=appkey)  # Always use sandbox
        self.setup_environment(config, app_name=appkey)
        
        # Set up JOBS_LAMBDA_FUNCTION_NAME environment variable
        direct_invoke_client = DirectInvokeClient("jobs")
        import os
        os.environ['JOBS_LAMBDA_FUNCTION_NAME'] = direct_invoke_client.function_name
        
        # Import here after environment is set up
        from app.clients.job_client import JobClient
        from app.jobs.core.sns_manager import SNSManager
        
        try:
            # Create clients
            job_client = JobClient()
            sns_manager = SNSManager()
            
            with self.console_utils.get_progress("Creating sync Maryland job...") as progress:
                task = progress.add_task("Processing...", total=None)
                
                # Create the job in the Jobs service (global job, not workspace-specific)
                job_record = job_client.create_job(
                    process_name='sync_maryland',
                    user_id=user_id
                )
                
                # Publish to SNS to trigger execution
                sns_manager.publish_message(
                    job_type="sync_maryland",
                    job_id=job_record.job_id,
                    params={
                        "appkey": appkey,
                        "session": session
                    },
                    user_id=user_id
                )
                
                progress.update(task, completed=True)
            
            self.console_utils.print_success("Sync Maryland job created successfully!")
            
            # Display job details
            job_data = {
                "Job ID": job_record.job_id,
                "Process": "sync_maryland",
                "Session": session,
                "App Key": appkey,
                "User": user_id,
                "Status": job_record.status
            }
            
            table = self.console_utils.create_status_table("Job Details", job_data)
            self.console.print(table)
            
            self.console.print(f"\n[bold yellow]Job ID: {job_record.job_id}[/bold yellow]")
            self.console.print(f"\n[blue]To check status, run:[/blue]")
            self.console.print(f"[cyan]./jobs.py status {job_record.job_id}[/cyan]")
            self.console.print("\n[blue]Check CloudWatch logs for detailed progress[/blue]")
            
        except Exception as e:
            self.console_utils.print_error(f"Failed to create sync Maryland job: {str(e)}")
            if verbose:
                self.handle_error(e, debug=True)
            raise typer.Exit(1)
    
    def list_jobs(self):
        """List available job types."""
        job_data = [
            {
                "job_type": "monitor_bills",
                "command": "jobs monitor",
                "description": "Monitor bills for changes and run AI analysis"
            },
            {
                "job_type": "sync_maryland",
                "command": "jobs sync",
                "description": "Sync Maryland legislative bills from official sources"
            }
        ]
        
        table = self.console_utils.create_list_table(
            job_data,
            title="Available Jobs",
            columns=["job_type", "command", "description"]
        )
        self.console.print(table)
    
    def check_status(self, job_id: str, developer_initials: Optional[str]):
        """Check the status of a job."""
        # Set developer initials override if provided
        if developer_initials:
            from utils import AppConfig
            AppConfig.set_developer_initials_override(developer_initials)
        
        # Load config and setup environment
        config = self.load_config()  # Always use sandbox
        # For status check, we only need credential store variables
        config.setup_environment(include_credential_store=True, env_filter=[])
        
        # Set up JOBS_LAMBDA_FUNCTION_NAME environment variable
        direct_invoke_client = DirectInvokeClient("jobs")
        import os
        os.environ['JOBS_LAMBDA_FUNCTION_NAME'] = direct_invoke_client.function_name
        
        # Import here after environment is set up
        from app.clients.job_client import JobClient
        
        try:
            job_client = JobClient()
            
            with self.console_utils.get_progress("Fetching job status...") as progress:
                task = progress.add_task("Loading...", total=None)
                
                # First try to get job at app level
                job = job_client.get_job(job_id)
                
                # If not found at app level, try workspace level with default org/ws
                if not job:
                    self.console.print("[yellow]Job not found at app level, checking workspace level...[/yellow]")
                    try:
                        # Try with default workspace (monitor jobs are typically workspace-level)
                        job = job_client.get_workspace_job("umd-org", "umd-ogc-state-ws", job_id)
                    except:
                        # If that fails, job truly doesn't exist
                        pass
                
                progress.update(task, completed=True)
            
            if not job:
                self.console_utils.print_error(
                    f"Job not found: {job_id}\n"
                    f"Checked both app-level and workspace-level (umd-org/umd-ogc-state-ws) endpoints.",
                    exit_code=1
                )
            
            # Display job details
            job_data = {
                "Job ID": job.job_id,
                "Process": job.process_name,
                "Status": self.console_utils.create_status_indicator(job.status),
                "Created": str(job.created_at)
            }
            
            if hasattr(job, 'updated_at') and job.updated_at:
                job_data["Updated"] = str(job.updated_at)
            if hasattr(job, 'org_id') and job.org_id:
                job_data["Organization"] = job.org_id
            if hasattr(job, 'ws_id') and job.ws_id:
                job_data["Workspace"] = job.ws_id
            
            table = self.console_utils.create_status_table("Job Status", job_data)
            self.console.print(table)
            
        except Exception as e:
            self.console_utils.print_error(f"Failed to get job status: {str(e)}", exit_code=1)


def main():
    """Main entry point."""
    cli = JobsCLI()
    cli.run()


if __name__ == "__main__":
    main()