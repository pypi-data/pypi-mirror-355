#!/usr/bin/env python3
"""
Unified client verification CLI for all API clients.
Tests direct Lambda invoke functionality for cost, job, and workspace clients.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
import os
import typer

# Add utils to path before other imports
import sys
sys.path.insert(0, str(Path(__file__).parent))

from utils import BaseCLI, ConfigUtils, DirectInvokeClient


class VerifyClientsCLI(BaseCLI):
    """CLI for verifying API client connectivity."""
    
    def __init__(self):
        super().__init__(
            name="verify-clients",
            help_text="Verify API client direct Lambda invoke functionality",
            require_config=True
        )
        
        # Get project root from config
        from utils import AppConfig
        self.doc_review_root = AppConfig.get_project_root()
        
        # Add commands
        self.setup_commands()
    
    def setup_commands(self):
        """Set up CLI commands."""
        
        @self.app.command()
        def cost(
            debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
        ):
            """Verify CostClient direct Lambda invoke."""
            self.verify_single_client("cost", debug)
        
        @self.app.command()
        def job(
            debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
        ):
            """Verify JobClient direct Lambda invoke."""
            self.verify_single_client("job", debug)
        
        @self.app.command()
        def workspace(
            debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
        ):
            """Verify WorkspacesClient direct Lambda invoke."""
            self.verify_single_client("workspace", debug)
        
        @self.app.command()
        def all(
            debug: bool = typer.Option(False, "--debug", "-d", help="Enable debug logging"),
            continue_on_error: bool = typer.Option(False, "--continue", help="Continue testing even if a client fails"),
        ):
            """Verify all clients (cost, job, and workspace)."""
            self.verify_all_clients(debug, continue_on_error)

        @self.app.command()
        def list():
            """List all available clients for verification."""
            self.list_clients()
    
    def setup_environment(self, config: ConfigUtils):
        """Set up environment for client testing."""
        # Determine which environment variables we actually need for client testing
        required_vars = []
        
        # API URLs - clients need these to connect
        api_url_vars = [
            'COST_API_URL', 'COSTS_API_URL',
            'JOB_API_URL', 'JOBS_API_URL', 
            'WORKSPACES_API_URL',
            'OIDC_MANAGER_API_URL'
        ]
        
        # Lambda function names - for direct invoke
        lambda_vars = [
            'COST_LAMBDA_FUNCTION_NAME',
            'JOB_LAMBDA_FUNCTION_NAME',
            'WORKSPACES_LAMBDA_FUNCTION_NAME',
            'LEGISLATIVE_REVIEW_LAMBDA_FUNCTION_NAME'
        ]
        
        # Other required variables from config files
        other_vars = [
            'OIDC_API_URL',  # May be needed for authentication
            'OIDC_CLIENT_ID',  # May be needed for client setup
            'AWS_REGION'  # Often needed for AWS SDK
        ]
        
        # Combine all required variables
        required_vars = api_url_vars + lambda_vars + other_vars
        
        # Only set the specific environment variables we need
        config.setup_environment(include_credential_store=True, env_filter=required_vars)
        
        # Normalize API URLs (handles COST vs COSTS, JOB vs JOBS)
        config.normalize_api_urls()
        
        # Discover and set Lambda function names using DirectInvokeClient
        self.setup_lambda_function_names()
        
        # Display API configuration
        api_data = {
            "Cost API": config.get_variable('COST_API_URL', 'Not set'),
            "Jobs API": config.get_variable('JOBS_API_URL', 'Not set'),
            "Workspaces API": config.get_variable('WORKSPACES_API_URL', 'Not set')
        }
        
        table = self.console_utils.create_status_table("API Configuration", api_data)
        self.console.print(table)
    
    def setup_lambda_function_names(self):
        """Discover and set Lambda function names for all clients."""
        # Map of client to environment variable
        from utils import AppConfig
        client_env_mapping = [
            (comp, AppConfig.get_component_lambda_env_var(comp))
            for comp in AppConfig.discover_components()
        ]
        
        for component, env_var in client_env_mapping:
            if not os.environ.get(env_var):
                try:
                    # Use DirectInvokeClient to discover the Lambda function name
                    direct_client = DirectInvokeClient(component)  # Always use sandbox
                    lambda_name = direct_client.function_name
                    os.environ[env_var] = lambda_name
                    self.logger.info(f"Set {env_var} = {lambda_name}")
                except Exception as e:
                    self.logger.warning(f"Could not discover Lambda function for {component}: {e}")
                    # Continue without failing - the individual test will fail if needed
    
    def verify_cost_client(self) -> bool:
        """Verify the CostClient functionality."""
        try:
            # Import here after environment is set up
            from app.clients.cost_client import CostClient
            
            self.console.print("\n[bold]Testing CostClient...[/bold]")
            
            # Create client
            client = CostClient()
            
            # Test: Create a simple cost entry
            self.console.print("Creating test cost entry...")
            result = client.create_cost(
                cost_type='TEXTRACT',
                amount='0.001',
                description=f'Test cost entry - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
                created_by='verify_clients'
            )
            
            self.console_utils.print_success("Cost created successfully")
            
            # Display results
            result_data = {
                "ID": result.PK,
                "Amount": f"${result.amount_usd}",
                "Type": result.cost_type,
                "Created": str(result.created_at)
            }
            
            table = self.console_utils.create_status_table("Cost Entry Details", result_data)
            self.console.print(table)
            
            return True
            
        except Exception as e:
            self.console_utils.print_error(f"CostClient test failed: {str(e)}")
            if self.logger.isEnabledFor(10):  # DEBUG level
                self.handle_error(e, debug=True)
            return False
    
    def verify_job_client(self) -> bool:
        """Verify the JobClient functionality."""
        try:
            # Import here after environment is set up
            from app.clients.job_client import JobClient
            
            self.console.print("\n[bold]Testing JobClient...[/bold]")
            
            # Create client
            client = JobClient()
            
            # Test: Create a workspace-level job
            self.console.print("Creating test job...")
            job = client.create_workspace_job(
                process_name='test_sync_bills',
                org_id='test-org-1',
                ws_id='test-ws-1',
                user_id='verify_clients'
            )
            
            self.console_utils.print_success("Job created successfully")
            
            # Display results
            result_data = {
                "ID": job.job_id,
                "Process": job.process_name,
                "Status": job.status,
                "Created": str(job.created_at)
            }
            
            table = self.console_utils.create_status_table("Job Details", result_data)
            self.console.print(table)
            
            return True
            
        except Exception as e:
            self.console_utils.print_error(f"JobClient test failed: {str(e)}")
            if self.logger.isEnabledFor(10):  # DEBUG level
                self.handle_error(e, debug=True)
            return False
    
    def verify_workspace_client(self) -> bool:
        """Verify the WorkspacesClient functionality."""
        try:
            # Import here after environment is set up
            from app.clients.workspaces_client import WorkspacesClient
            
            self.console.print("\n[bold]Testing WorkspacesClient...[/bold]")
            
            # Create client
            client = WorkspacesClient()
            
            # Test: Check workspace access
            self.console.print("Checking workspace access...")
            access = client.check_workspace_access(
                org_id='ogc-default-org-1',
                ws_id='maryland-default-ws-1',
                user_id='verify_clients'
            )
            
            self.console_utils.print_success("Access check completed successfully")
            
            if access:
                result_data = {
                    "Has Access": str(access.get('has_access', False)),
                    "Role": access.get('role', 'None')
                }
            else:
                result_data = {
                    "Result": "No access information returned",
                    "Note": "User may not have access to this workspace"
                }
            
            table = self.console_utils.create_status_table("Access Check Results", result_data)
            self.console.print(table)
            
            return True
            
        except Exception as e:
            self.console_utils.print_error(f"WorkspacesClient test failed: {str(e)}")
            if self.logger.isEnabledFor(10):  # DEBUG level
                self.handle_error(e, debug=True)
            return False
    
    def verify_single_client(self, client_type: str, debug: bool):
        """Verify a single client."""
        if debug:
            self.setup_logging("DEBUG")
        
        # Load config and setup environment
        config = self.load_config()  # Always use sandbox
        self.setup_environment(config)
        
        # Map client types to verification methods
        client_map = {
            "cost": (self.verify_cost_client, "CostClient"),
            "job": (self.verify_job_client, "JobClient"),
            "workspace": (self.verify_workspace_client, "WorkspacesClient")
        }
        
        verify_func, client_name = client_map[client_type]
        success = verify_func()
        
        if success:
            self.console_utils.print_success(f"{client_name} direct Lambda invoke is working correctly!")
        else:
            self.console_utils.print_error(f"{client_name} verification failed", exit_code=1)
    
    def verify_all_clients(self, debug: bool, continue_on_error: bool):
        """Verify all clients."""
        if debug:
            self.setup_logging("DEBUG")
        
        # Load config and setup environment
        config = self.load_config()  # Always use sandbox
        self.setup_environment(config)
        
        self.console.print("[bold]Verifying all clients...[/bold]")
        
        results: List[Tuple[str, bool]] = []
        clients = [
            ("CostClient", self.verify_cost_client),
            ("JobClient", self.verify_job_client),
            ("WorkspacesClient", self.verify_workspace_client),
        ]
        
        for client_name, verify_func in clients:
            success = verify_func()
            results.append((client_name, success))
            
            if not success and not continue_on_error:
                self.console_utils.print_error(f"Stopping after {client_name} failure")
                break
        
        # Display summary
        all_success = self.display_results(results, "Verification Summary")
        
        if not all_success:
            raise typer.Exit(1)
    
    def list_clients(self):
        """List all available clients for verification."""
        client_data = [
            {
                "client": "CostClient",
                "command": "verify-clients cost",
                "description": "Verify cost tracking API client"
            },
            {
                "client": "JobClient",
                "command": "verify-clients job",
                "description": "Verify job processing API client"
            },
            {
                "client": "WorkspacesClient",
                "command": "verify-clients workspace",
                "description": "Verify workspace management API client"
            },
            {
                "client": "All",
                "command": "verify-clients all",
                "description": "Verify all clients"
            }
        ]
        
        table = self.console_utils.create_list_table(
            client_data,
            title="Available Clients",
            columns=["client", "command", "description"]
        )
        self.console.print(table)


def main():
    """Main entry point."""
    cli = VerifyClientsCLI()
    cli.run()


if __name__ == "__main__":
    main()