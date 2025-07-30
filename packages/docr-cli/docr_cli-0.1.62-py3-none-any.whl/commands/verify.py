"""Verify client connections and functionality."""
import subprocess
import sys
import os
from pathlib import Path
import typer

from utils import AppConfig, ConsoleUtils


def verify_client():
    """Verify API clients by testing cost, job, and workspace clients from current backend directory."""
    console_utils = ConsoleUtils()
    
    # Verify it's a valid backend directory with samconfig.toml
    cwd = Path.cwd()
    if not (cwd / "samconfig.toml").exists():
        console_utils.print_error(
            f"Not a valid backend directory: {cwd}\n"
            f"Missing samconfig.toml file.\n"
            f"Please navigate to a backend directory and run the command again.",
            exit_code=1
        )
    
    # Use current directory as backend directory
    backend_dir = cwd
    console_utils.print_info(f"Testing API clients from: {backend_dir}")
    
    try:
        # Read config file to get environment variables
        config_file = backend_dir / "config" / "config.sandbox"
        if not config_file.exists():
            console_utils.print_error(
                f"Config file not found: {config_file}\n"
                "Make sure config.sandbox exists in the backend directory.",
                exit_code=1
            )
        
        # Parse config file and set environment variables
        env_vars = {}
        
        with open(config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    env_vars[key] = value
        
        # Get developer initials from TOML config
        developer_initials = AppConfig.get_developer_initials()
        
        console_utils.print_info(f"Using developer initials: {developer_initials}")
        
        # Discover Lambda function names using AWS CLI
        lambda_functions = {}
        stack_patterns = [
            ("costs-app", "COST_LAMBDA_FUNCTION_NAME"),
            ("jobs-app", "JOB_LAMBDA_FUNCTION_NAME"),
            ("workspaces-app", "WORKSPACES_LAMBDA_FUNCTION_NAME")
        ]
        
        for stack_prefix, env_var_name in stack_patterns:
            stack_name = f"{stack_prefix}-{developer_initials}"
            try:
                cmd = [
                    "aws", "cloudformation", "describe-stacks",
                    "--stack-name", stack_name,
                    "--query", "Stacks[0].Outputs[?OutputKey=='FastSyncLambdaName'].OutputValue",
                    "--output", "text"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout.strip():
                    lambda_name = result.stdout.strip()
                    lambda_functions[env_var_name] = lambda_name
                    console_utils.print_info(f"Found {env_var_name}: {lambda_name}")
                else:
                    console_utils.print_warning(f"Could not find Lambda for stack: {stack_name}")
            except Exception as e:
                console_utils.print_warning(f"Error looking up {stack_name}: {e}")
        
        # Add discovered Lambda functions to environment variables
        env_vars.update(lambda_functions)
        
        console_utils.print_info(f"Loaded {len(env_vars)} environment variables from config and AWS")
        
        # Test each client with a simple import and basic operation
        clients_to_test = [
            ("Cost Client", "cost_client", "CostClient"),
            ("Job Client", "job_client", "JobClient"), 
            ("Workspace Client", "workspaces_client", "WorkspacesClient")
        ]
        
        for client_name, module_name, class_name in clients_to_test:
            console_utils.print_step(clients_to_test.index((client_name, module_name, class_name)) + 1, 
                                   len(clients_to_test), f"Testing {client_name}")
            
            # Create Python code to test the client
            test_code = f'''
import sys
sys.path.insert(0, ".")
try:
    from app.clients.{module_name} import {class_name}
    client = {class_name}()
    print("✅ {client_name}: Import and instantiation successful")
except Exception as e:
    print(f"❌ {client_name}: {{e}}")
    sys.exit(1)
'''
            
            # Run the test via poetry with environment variables
            cmd = ["poetry", "run", "python", "-c", test_code]
            
            # Combine current environment with config variables
            test_env = os.environ.copy()
            test_env.update(env_vars)
            
            result = subprocess.run(cmd, cwd=backend_dir, capture_output=True, text=True, env=test_env)
            
            if result.returncode == 0:
                console_utils.print_success(f"{client_name} verification passed")
                if result.stdout.strip():
                    print(result.stdout.strip())
            else:
                console_utils.print_error(f"{client_name} verification failed")
                if result.stderr.strip():
                    print(result.stderr.strip())
                if result.stdout.strip():
                    print(result.stdout.strip())
                raise typer.Exit(1)
        
        console_utils.print_success("All API client verifications completed successfully!")
            
    except Exception as e:
        console_utils.print_error(f"Error running client verification: {str(e)}")
        raise typer.Exit(1)