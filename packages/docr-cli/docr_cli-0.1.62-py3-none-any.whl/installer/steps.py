"""Installation step definitions for the Document Review system."""

from typing import List, Dict
from pathlib import Path
from utils import AppConfig
from rich.table import Table
from rich import box
from utils.shared_console import get_shared_console


class InstallationSteps:
    """Manage installation steps for the Document Review system."""
    
    def __init__(self):
        self.console = get_shared_console()
    
    def get_installation_steps(self, skip_frontend: bool = False) -> List[Dict]:
        """Get all installation steps."""
        return get_installation_steps(skip_frontend)
    
    def list_installation_steps(self, skip_frontend: bool = False):
        """Display all installation steps in a table."""
        steps = self.get_installation_steps(skip_frontend)
        
        table = Table(title="Installation Steps", box=box.SIMPLE, show_lines=True)
        table.add_column("Step Name", style="green", width=35)
        table.add_column("What It Does", style="yellow", width=55)
        table.add_column("Command", style="blue", width=60)
        table.add_column("Subprocess Commands", style="magenta", width=70)
        
        for i, step in enumerate(steps, 1):
            # Build the main command
            main_cmd = " ".join(step["command"])
            
            # Add cwd if present
            if step.get("cwd"):
                cwd_path = step["cwd"]
                if callable(cwd_path):
                    cwd_path = str(cwd_path())
                main_cmd = f"cd {cwd_path} && {main_cmd}"
            
            # Add chain commands
            if step.get("chain"):
                for chain_cmd in step["chain"]:
                    main_cmd += " && " + " ".join(chain_cmd)
            
            # Build subprocess commands list
            subprocess_cmds = []
            
            # Expand docr commands to show what they actually do
            if "docr" in step["command"][0]:
                cmd_str = " ".join(step["command"])
                if "config backend --all" in cmd_str:
                    subprocess_cmds = ["no subprocess - only file writes"]
                elif "config backend" in cmd_str and "--all" not in cmd_str:
                    subprocess_cmds = ["no subprocess - only file writes"]
                elif "config frontend" in cmd_str:
                    subprocess_cmds = ["no subprocess - only file writes"]
                elif "deploy backend" in cmd_str:
                    subprocess_cmds = ["poetry --version", "poetry check --lock", "aws lambda get-function", 
                                      "aws ecr get-login-password | docker login", "sam build --use-container",
                                      "docker tag", "docker push", "aws lambda update-function-code"]
                elif "deploy frontend" in cmd_str and "--full" in cmd_str:
                    subprocess_cmds = ["npm install", "npm run build -- --mode production", 
                                      "sam deploy --capabilities CAPABILITY_IAM", "aws s3 sync",
                                      "aws cloudfront create-invalidation"]
                elif "deploy frontend" in cmd_str and "--full" not in cmd_str:
                    subprocess_cmds = ["npm install", "npm run build -- --mode production",
                                      "aws s3 sync", "aws cloudfront create-invalidation"]
                elif "bootstrap all" in cmd_str:
                    subprocess_cmds = ["boto3: cloudformation.describe_stacks", "HTTP POST to API endpoints"]
                elif "refresh" in cmd_str:
                    subprocess_cmds = ["boto3: sts.get_caller_identity", "boto3: cloudformation.describe_stacks"]
                elif "oidc register" in cmd_str:
                    subprocess_cmds = ["node add-client.js --help", "npm install (if needed)",
                                      "node add-api-clients.js", "node add-client.js"]
                elif "jobs sync" in cmd_str:
                    subprocess_cmds = ["boto3: lambda.invoke", "boto3: sns.publish"]
                elif "jobs monitor" in cmd_str:
                    subprocess_cmds = ["boto3: lambda.invoke", "boto3: sns.publish"]
                elif "credstore add-from-ssm" in cmd_str:
                    subprocess_cmds = ["aws cloudformation list-stacks --page-size 1",
                                      "boto3: ssm.get_parameter", "credential store API"]
                elif "doctor all" in cmd_str:
                    subprocess_cmds = ["aws cloudformation describe-stacks --query StackStatus",
                                      "file validation", "API connectivity tests"]
                elif "show-urls" in cmd_str:
                    subprocess_cmds = ["calls docr refresh", "reads ~/docr.toml"]
            elif "sam build" in main_cmd:
                subprocess_cmds = ["docker run lambci/lambda:build", "pip install -r requirements.txt"]
            elif "sam deploy" in main_cmd:
                subprocess_cmds = ["aws cloudformation package", "aws cloudformation deploy",
                                  "aws cloudformation wait"]
            elif "npm install" in main_cmd:
                subprocess_cmds = ["downloads packages from npm/CodeArtifact"]
            elif "aws cloudformation list-stacks" in main_cmd:
                subprocess_cmds = ["direct AWS CLI call"]
            elif "sleep" in main_cmd:
                subprocess_cmds = ["OS sleep call"]
            
            # Format subprocess commands
            if subprocess_cmds:
                if len(subprocess_cmds) == 1:
                    subprocess_display = subprocess_cmds[0]
                elif len(subprocess_cmds) <= 3:
                    subprocess_display = " → ".join(subprocess_cmds)
                else:
                    subprocess_display = " → ".join(subprocess_cmds[:2]) + f" → ... ({len(subprocess_cmds)-2} more)"
            else:
                subprocess_display = "-"
            
            table.add_row(
                f"{i:2d}. {step['name']}",
                step["description"],
                f"[dim]{main_cmd}[/dim]",
                f"[dim]{subprocess_display}[/dim]"
            )
        
        self.console.print(table)
        self.console.print(f"\n[bold]Total steps: {len(steps)}[/bold]")
        if skip_frontend:
            self.console.print("[yellow]Note: Frontend deployment steps excluded[/yellow]")


def get_installation_steps(skip_frontend: bool = False) -> List[Dict]:
    """Define all installation steps with their commands and wait conditions."""
    
    initials = AppConfig.get_developer_initials()
    
    steps = [
        {
            "name": "Initial Setup",
            "description": "Creates project config at ~/docr.toml, sets developer initials and project root",
            "command": ["docr", "setup"],
            "check": lambda: AppConfig.CONFIG_FILE.exists(),
            "skip_if_complete": True
        },
        {
            "name": "Configure All Backends",
            "description": "Generates samconfig.toml files for all components with stack names and parameters",
            "command": ["docr", "config", "backend", "--all"],
            "wait": None  # No CloudFormation wait needed
        },
        {
            "name": "Deploy OIDC Authorizer",
            "description": "Builds and deploys Lambda authorizer for JWT validation across all APIs",
            "command": ["sam", "build"],
            "cwd": _get_component_path("oidc-oidcauthorizer-serverless"),
            "chain": [
                ["sam", "deploy", "--no-confirm-changeset"]
            ],
            "wait": {
                "stack_name": f"oidc-lambda-authorizer-shared-{initials}",
                "wait_type": "create_or_update"
            }
        },
        {
            "name": "Deploy Cost Component",
            "description": "Builds FastAPI service for cost tracking, creates DynamoDB tables and Lambda functions",
            "command": ["sam", "build"],
            "cwd": _get_component_path("aisolutions-costsmodule-serverless/cost-component-backend"),
            "chain": [
                ["sam", "deploy", "--no-confirm-changeset"]
            ],
            "wait": {
                "stack_name": f"costs-app-{initials}",
                "wait_type": "create_or_update"
            }
        },
        {
            "name": "Deploy Jobs Component",
            "description": "Builds job processing service with SQS queues, SNS topics for async processing",
            "command": ["sam", "build"],
            "cwd": _get_component_path("aisolutions-jobsmodule-serverless/jobs-component-backend"),
            "chain": [
                ["sam", "deploy", "--no-confirm-changeset"]
            ],
            "wait": {
                "stack_name": f"jobs-app-{initials}",
                "wait_type": "create_or_update"
            }
        },
        {
            "name": "Deploy Workspaces Component",
            "description": "Builds workspace management API with organization/workspace data models",
            "command": ["sam", "build"],
            "cwd": _get_component_path("aisolutions-workspaces-serverless/workspaces-component-backend"),
            "chain": [
                ["sam", "deploy", "--no-confirm-changeset"]
            ],
            "wait": {
                "stack_name": f"workspaces-app-{initials}",
                "wait_type": "create_or_update"
            }
        },
        {
            "name": "Refresh Configuration",
            "description": "Fetches CloudFormation outputs (API URLs, ARNs) and updates ~/docr.toml",
            "command": ["docr", "refresh"],
            "wait": None
        },
        {
            "name": "Generate OIDC Manager Config",
            "description": "Creates config files with component API URLs from CloudFormation outputs",
            "command": ["docr", "config", "backend", "oidc-manager"],
            "wait": None
        },
        {
            "name": "Deploy OIDC Manager Application",
            "description": "Builds OIDC client management service with DynamoDB table for client registrations",
            "command": ["sam", "build"],
            "cwd": _get_component_path("oidc-oidcmanager-serverless/oidc-manager-backend"),
            "chain": [
                ["sam", "deploy", "--no-confirm-changeset"]
            ],
            "wait": {
                "stack_name": f"oidc-app-{initials}",
                "wait_type": "create_or_update"
            }
        },
        {
            "name": "Update OIDC Manager Config",
            "description": "Re-generates config with latest API URLs and table names from stack outputs",
            "command": ["docr", "config", "backend", "oidc-manager", "--force"],
            "wait": None
        },
        {
            "name": "Generate Legislative Review Config",
            "description": "Creates env config with component API URLs for service integration",
            "command": ["docr", "config", "backend", "legislative-review"],
            "wait": None
        },
        {
            "name": "Deploy Legislative Review Application",
            "description": "Builds main app with S3 bucket, Lambda functions, and API Gateway endpoints",
            "command": ["sam", "build"],
            "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-backend"),
            "chain": [
                ["sam", "deploy", "--no-confirm-changeset"]
            ],
            "wait": {
                "stack_name": f"legislative-review-{initials}",
                "wait_type": "create_or_update"
            }
        },
        {
            "name": "Update Legislative Review Config",
            "description": "Updates config with S3 bucket names and Lambda ARNs from deployment",
            "command": ["docr", "config", "backend", "legislative-review", "--force"],
            "wait": None
        },
        {
            "name": "Final Refresh",
            "description": "Final sync of all CloudFormation outputs to ~/docr.toml configuration",
            "command": ["docr", "refresh"],
            "wait": None
        },
        {
            "name": "Install OIDC Scripts Dependencies",
            "description": "Installs Node.js packages required for OIDC client registration scripts",
            "command": ["npm", "install", "--progress=true", "--loglevel=info"],
            "cwd": _get_component_path("oidc-oidcauthorizer-serverless"),
            "wait": None
        },
        {
            "name": "Register Legislative Review OIDC Client",
            "description": "Creates OIDC client entry in DynamoDB with redirect URIs and client credentials",
            "command": ["docr", "oidc", "register", "--app", "legislative-review"],
            "wait": None
        },
        {
            "name": "Register OIDC Manager Client",
            "description": "Self-registers OIDC Manager app for authentication to its own endpoints",
            "command": ["docr", "oidc", "register", "--app", "oidc-manager"],
            "wait": None
        },
        {
            "name": "Wait for OIDC Registration Sync",
            "description": "Pauses to ensure DynamoDB entries propagate before frontend config generation",
            "command": ["sleep", "15"],
            "wait": None
        }
    ]
    
    if not skip_frontend:
        steps.extend([
            {
                "name": "Generate Legislative Review Frontend Config",
                "description": "Creates .env.production with API URLs and OIDC client ID from registrations",
                "command": ["docr", "config", "frontend", "--app", "legislative-review", "--force"],
                "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-frontend"),
                "wait": None
            },
            {
                "name": "Generate OIDC Manager Frontend Config",
                "description": "Creates .env.production with API URLs and OIDC client ID from registrations",
                "command": ["docr", "config", "frontend", "--app", "oidc-manager", "--force"],
                "cwd": _get_component_path("oidc-oidcmanager-serverless/oidc-manager-frontend"),
                "wait": None
            },
            {
                "name": "Deploy Legislative Review Frontend",
                "description": "Builds React app, creates S3 bucket and CloudFront distribution with HTTPS",
                "command": ["docr", "deploy", "frontend", "--app", "legislative-review", "--full", "--verbose"],
                "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-frontend"),
                "wait": {
                    "stack_name": f"legislative-review-frontend-{initials}",
                    "wait_type": "create_or_update",
                    "timeout": 900  # 15 minutes for CloudFront
                }
            },
            {
                "name": "Deploy OIDC Manager Frontend",
                "description": "Builds React app, creates S3 bucket and CloudFront distribution with HTTPS",
                "command": ["docr", "deploy", "frontend", "--app", "oidc-manager", "--full", "--verbose"],
                "cwd": _get_component_path("oidc-oidcmanager-serverless/oidc-manager-frontend"),
                "wait": {
                    "stack_name": f"oidc-manager-{initials}",
                    "wait_type": "create_or_update",
                    "timeout": 900  # 15 minutes for CloudFront
                }
            },
            {
                "name": "Generate Legislative Review Frontend Config for S3",
                "description": "Regenerates .env.production with CloudFront URLs for proper CORS configuration",
                "command": ["docr", "config", "frontend", "--app", "legislative-review", "--force"],
                "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-frontend"),
                "wait": None
            },
            {
                "name": "Generate OIDC Manager Frontend Config for S3",
                "description": "Regenerates .env.production with CloudFront URLs for proper CORS configuration",
                "command": ["docr", "config", "frontend", "--app", "oidc-manager", "--force"],
                "cwd": _get_component_path("oidc-oidcmanager-serverless/oidc-manager-frontend"),
                "wait": None
            },
            {
                "name": "Deploy Legislative Review Frontend to S3",
                "description": "Syncs built React files to S3 bucket and invalidates CloudFront cache",
                "command": ["docr", "deploy", "frontend", "--app", "legislative-review", "--verbose"],
                "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-frontend"),
                "wait": None
            },
            {
                "name": "Deploy OIDC Manager Frontend to S3",
                "description": "Syncs built React files to S3 bucket and invalidates CloudFront cache",
                "command": ["docr", "deploy", "frontend", "--app", "oidc-manager", "--verbose"],
                "cwd": _get_component_path("oidc-oidcmanager-serverless/oidc-manager-frontend"),
                "wait": None
            }
        ])
    
    # Add final cleanup steps to ensure configs are correct
    steps.extend([
        {
            "name": "Final OIDC Manager Config Update",
            "description": "Final config sync to ensure all API URLs and table names are current",
            "command": ["docr", "config", "backend", "oidc-manager", "--force"],
            "wait": None
        },
        {
            "name": "Final OIDC Manager Deploy",
            "description": "Builds Docker image, pushes to ECR, updates Lambda with latest code",
            "command": ["docr", "deploy", "backend", "--app", "oidc-manager"],
            "wait": None
        },
        {
            "name": "Final Legislative Review Config Update", 
            "description": "Final config sync to ensure all component API URLs are current",
            "command": ["docr", "config", "backend", "legislative-review", "--force"],
            "wait": None
        }
    ])
    
    steps.extend([
        {
            "name": "Bootstrap Components",
            "description": "Loads YAML fixtures: organizations, workspaces, users, and sample bills",
            "command": ["docr", "bootstrap", "all", "--app", "legislative-review", "--verbose"],
            "wait": None
        },
        {
            "name": "Trigger Sync Job",
            "description": "Fetches Maryland bills from API, processes with AI, stores in DynamoDB",
            "command": ["docr", "jobs", "sync", "--session", "2025RS", "--app", "legislative-review", "--verbose"],
            "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-backend"),
            "wait": None
        },
        {
            "name": "Wait for Sync Processing",
            "description": "Waits for async job processing of bills through SQS/Lambda pipeline",
            "command": ["sleep", "30"],
            "wait": None
        },
        {
            "name": "Trigger Monitor Job",
            "description": "Triggers AI analysis job to monitor bills for UMD policy impacts",
            "command": ["docr", "jobs", "monitor", "--app", "legislative-review", "--org", "umd-org", "--workspace", "umd-ogc-state-ws", "--verbose"],
            "cwd": _get_component_path("aisolutions-docreview-serverless/legislative-review-backend"),
            "wait": None
        },
        {
            "name": "Setup OpenAI API Key",
            "description": "Retrieves OpenAI key from SSM and stores in mock credential store",
            "command": ["docr", "credstore", "add-from-ssm", "openai"],
            "wait": None
        },
        {
            "name": "Final Verification",
            "description": "Displays all CloudFormation stacks in table format for verification",
            "command": ["aws", "cloudformation", "list-stacks", "--stack-status-filter", "CREATE_COMPLETE", "UPDATE_COMPLETE", "--output", "table"],
            "wait": None
        },
        {
            "name": "System Health Check",
            "description": "Validates stacks, configs, OIDC clients, and API connectivity",
            "command": ["docr", "doctor", "all"],
            "wait": None
        },
        {
            "name": "Display Application URLs",
            "description": "Displays frontend URLs and default login credentials for easy access",
            "command": ["docr", "show-urls"],
            "wait": None
        }
    ])
    
    return steps


def _get_component_path(component: str) -> Path:
    """Get the full path to a component directory."""
    config = AppConfig.load_config()
    # Get project root from config - it's stored under 'project.root'
    project_data = config.get('project', {})
    project_root = Path(project_data.get('root', Path.cwd()))
    return project_root / component