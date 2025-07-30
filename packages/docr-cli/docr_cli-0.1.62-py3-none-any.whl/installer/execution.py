"""Step execution logic for the installation process."""

import subprocess
import boto3
import time
import os
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TimeElapsedColumn
from utils.shared_console import get_shared_console


class StepExecutor:
    """Handle execution of installation steps."""
    
    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.console = get_shared_console()
        self.cf_client = boto3.client('cloudformation')
        
    def execute_installation(self, steps: List[Dict], start_step: int, progress_file: Path, 
                           total_original_steps: int, ui, completed_steps: List, 
                           failed_steps: List, last_step_num_ref: List) -> bool:
        """Execute installation with progress tracking."""
        total_steps = total_original_steps or len(steps)
        
        self.console.print("\n[bold green]Starting installation...[/bold green]\n")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            
            # Create overall progress task
            overall_task = progress.add_task(
                "[cyan]Overall Progress", 
                total=len(steps)  # Use actual number of steps to process
            )
            
            # Process each step
            for i, step in enumerate(steps):
                step_num = i + start_step
                
                # Update overall progress description
                progress.update(
                    overall_task, 
                    description=f"[cyan]Step {step_num}: {step['name']}"
                )
                
                # Log step start
                self._log(f"\n{'='*80}")
                self._log(f"STEP {step_num}: {step['name']}")
                self._log(f"Description: {step['description']}")
                self._log(f"Started at: {datetime.now().isoformat()}")
                self._log(f"{'='*80}\n")
                
                try:
                    # Show step panel
                    ui.show_step_start(step_num, step, total_steps)
                    
                    # Execute the step
                    success = self._execute_step_with_output(step, step_num)
                    
                    if success:
                        completed_steps.append(step)
                        last_step_num_ref[0] = step_num
                        self._save_progress(progress_file, step_num)
                        self._log(f"\nStep {step_num} completed successfully at {datetime.now().isoformat()}\n")
                        ui.show_step_complete(step_num, step)
                    else:
                        raise Exception("Step execution failed")
                        
                except Exception as e:
                    failed_steps.append(step)
                    ui.show_step_failed(step_num, step, str(e), self.log_file)
                    self._log(f"\nERROR at step {step_num}: {str(e)}")
                    self._log(f"Failed at: {datetime.now().isoformat()}")
                    
                    self.console.print(f"\n[red]Resume with: docr install --resume-from {step_num}[/red]")
                    return False
                
                # Update progress
                progress.update(overall_task, advance=1)
        
        return True
        
    def _execute_step_with_output(self, step: Dict, step_num: int) -> bool:
        """Execute a step and show real-time output."""
        # Check if step should be skipped
        if step.get('skip_if_complete') and step.get('check', lambda: False)():
            self.console.print("[yellow]Step already complete, skipping[/yellow]")
            self._log("Step already complete, skipping")
            return True
        
        # Execute command
        if 'command' in step:
            cwd = step.get('cwd', None)
            cmd_str = ' '.join(step['command'])
            
            self._log(f"Executing command: {cmd_str}")
            if cwd:
                self._log(f"Working directory: {cwd}")
                # Ensure npm authentication works for Node.js projects
                self._ensure_npm_auth(Path(cwd))
            
            # Show command being executed
            self.console.print(f"[bold cyan]$ {cmd_str}[/bold cyan]")
            
            # Execute with real-time output and token retry
            success = self._run_command_with_token_retry(step['command'], cwd)
            
            if not success:
                return False
                
            # Execute chained commands
            for chain_cmd in step.get('chain', []):
                chain_str = ' '.join(chain_cmd)
                self._log(f"\nExecuting chained command: {chain_str}")
                self.console.print(f"[bold cyan]$ {chain_str}[/bold cyan]")
                
                success = self._run_command_with_token_retry(chain_cmd, cwd)
                if not success:
                    return False
        
        # Wait for CloudFormation if specified
        if 'wait' in step and step['wait']:
            wait_config = step['wait']
            self._wait_for_stack_with_progress(
                wait_config['stack_name'],
                wait_config['wait_type'],
                wait_config.get('timeout', 600)
            )
        
        # Post-process output if specified
        if 'post_process' in step:
            step['post_process']("")  # We don't have stdout captured anymore
            
        return True
        
    def _ensure_npm_auth(self, cwd: Path) -> None:
        """Ensure npm authentication will work by removing package-lock.json.
        
        When using AWS CodeArtifact, package-lock.json can contain outdated auth tokens
        that cause npm install to fail with 401 errors during Docker builds.
        Removing package-lock.json forces npm to use the current authentication
        from the user's ~/.npmrc file instead of cached credentials.
        """
        if cwd and cwd.exists():
            # Check if this directory has a package.json
            package_json = cwd / "package.json"
            package_lock = cwd / "package-lock.json"
            
            if package_json.exists() and package_lock.exists():
                # Delete package-lock.json to fix CodeArtifact authentication issues
                self._log(f"Removing package-lock.json to fix CodeArtifact auth token issues")
                self.console.print(f"[dim]Removing package-lock.json to fix CodeArtifact authentication[/dim]")
                try:
                    package_lock.unlink()
                    self._log(f"Successfully removed {package_lock}")
                except Exception as e:
                    self._log(f"Warning: Could not remove package-lock.json: {e}")
                    self.console.print(f"[yellow]Warning: Could not remove package-lock.json: {e}[/yellow]")
                    
    def _run_command_with_token_retry(self, command: List[str], cwd: Optional[Path] = None) -> bool:
        """Run command with automatic retry on AWS token expiration and ECR timeout errors."""
        # First attempt
        result = self._run_command_with_output(command, cwd)
        
        # If successful, return True
        if result:
            return True
            
        # Check if this was a token expiration error or ECR timeout error
        # The _run_command_with_output method now detects ExpiredToken in output
        # and returns False if found, so we check the log for confirmation
        try:
            with open(self.log_file, 'r') as f:
                log_content = f.read()
                # Check last 5000 chars for errors (increased to catch ECR errors)
                recent_content = log_content[-5000:]
                
                # Check for expired token
                if 'ExpiredToken' in recent_content:
                    self._log("Confirmed expired token error, waiting 5 seconds for auto-refresh...")
                    self.console.print("[yellow]⚠️  AWS token expired, waiting 5 seconds for auto-refresh...[/yellow]")
                    time.sleep(5)
                    
                    # Recreate boto3 clients to pick up new credentials
                    self.cf_client = boto3.client('cloudformation')
                    
                    # Retry the command
                    self._log("Retrying command after token refresh...")
                    return self._run_command_with_output(command, cwd)
                
                # Check for ECR timeout errors (common AWS issue)
                elif ('dial tcp' in recent_content and 'i/o timeout' in recent_content and 
                      ('.dkr.ecr.' in recent_content or 'proxyconnect' in recent_content)):
                    self._log("Detected ECR connection timeout error, retrying in 10 seconds...")
                    self.console.print("[yellow]⚠️  ECR connection timeout detected (common AWS issue), retrying in 10 seconds...[/yellow]")
                    time.sleep(10)
                    
                    # Retry the command
                    self._log("Retrying command after ECR timeout...")
                    return self._run_command_with_output(command, cwd)
                    
        except Exception as e:
            self._log(f"Error checking for retryable errors: {str(e)}")
        
        # If not a retryable error or retry failed, return the original failure
        return False
        
    def _run_command_with_output(self, command: List[str], cwd: Optional[Path] = None) -> bool:
        """Run command and stream ALL output for debugging.
        
        IMPORTANT: This method shows FULL output from all commands.
        Nothing is filtered or hidden - everything goes to both console and log file.
        """
        try:
            # Set environment variable to signal subprocess mode
            env = os.environ.copy()
            env['DOCR_SUBPROCESS'] = 'true'
            
            # Add visual separator for command output
            self.console.print(f"[dim]{'─' * 80}[/dim]")
            
            process = subprocess.Popen(
                command,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Stream output and check for token expiration and ECR timeouts
            output_lines = []
            has_expired_token = False
            has_ecr_timeout = False
            
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    # Log the line
                    self._log(line)
                    
                    # Check for expired token in output
                    if 'ExpiredToken' in line:
                        has_expired_token = True
                        self._log("DETECTED: ExpiredToken error in subprocess output")
                    
                    # Check for ECR timeout errors
                    if 'dial tcp' in line and 'i/o timeout' in line and ('.dkr.ecr.' in line or 'proxyconnect' in line):
                        has_ecr_timeout = True
                        self._log("DETECTED: ECR timeout error in subprocess output")
                    
                    # Show ALL output - no filtering!
                    if self._should_show_line(line):
                        # Color error lines red, warning lines yellow
                        if 'error' in line.lower() or 'fail' in line.lower():
                            self.console.print(f"[red]{line}[/red]")
                        elif 'warning' in line.lower() or 'warn' in line.lower():
                            self.console.print(f"[yellow]{line}[/yellow]")
                        else:
                            self.console.print(line)
                    output_lines.append(line)
            
            process.wait()
            
            # Add visual separator at end of command output
            self.console.print(f"[dim]{'─' * 80}[/dim]")
            
            # If we detected an expired token error, set return code to indicate failure
            if has_expired_token:
                self._log("ExpiredToken detected in output - marking command as failed for retry")
                return False
            
            # If we detected an ECR timeout error, set return code to indicate failure
            if has_ecr_timeout:
                self._log("ECR timeout detected in output - marking command as failed for retry")
                return False
            
            if process.returncode != 0:
                self._log(f"Command failed with exit code {process.returncode}")
                self.console.print(f"[red]Command failed with exit code {process.returncode}[/red]")
                return False
                
            return True
            
        except Exception as e:
            self._log(f"Command execution error: {str(e)}")
            return False
            
    def _should_show_line(self, line: str) -> bool:
        """Determine if a line should be shown in console output.
        
        IMPORTANT: This method ALWAYS returns True to ensure FULL output visibility.
        We show EVERYTHING for debugging on developer machines.
        No filtering, no hiding, complete transparency!
        """
        # ALWAYS SHOW ALL OUTPUT - NO EXCEPTIONS!
        return True
        
    def _wait_for_stack_with_progress(self, stack_name: str, wait_type: str, timeout: int = 600):
        """Wait for CloudFormation stack with progress display."""
        self.console.print(f"\n[yellow]⏳ Waiting for CloudFormation stack: {stack_name}[/yellow]")
        self._log(f"\nWaiting for CloudFormation stack: {stack_name}")
        self._log(f"Wait type: {wait_type}, Timeout: {timeout} seconds")
        
        start_time = datetime.now()
        max_attempts = timeout // 10  # Check every 10 seconds
        
        # Use simple polling without status display to avoid conflict with Progress
        for attempt in range(max_attempts):
            try:
                response = self.cf_client.describe_stacks(StackName=stack_name)
                stack_status = response['Stacks'][0]['StackStatus']
                
                # Log status updates
                elapsed = datetime.now() - start_time
                self._log(f"Stack status: {stack_status} ({elapsed.seconds}s elapsed)")
                
                # Check if complete
                if 'COMPLETE' in stack_status and 'IN_PROGRESS' not in stack_status:
                    if 'FAILED' in stack_status or 'ROLLBACK' in stack_status:
                        self._log(f"Stack deployment failed with status: {stack_status}")
                        raise Exception(f"Stack {stack_name} failed with status: {stack_status}")
                    else:
                        self._log(f"Stack deployment completed with status: {stack_status}")
                        self.console.print(f"[green]✅ Stack {stack_name} deployed successfully![/green]")
                        return
                
                # Still in progress
                time.sleep(10)
                
            except self.cf_client.exceptions.ClientError as e:
                if 'does not exist' in str(e):
                    # Stack doesn't exist yet, keep waiting
                    self._log("Waiting for stack creation to start...")
                    time.sleep(10)
                elif 'ExpiredToken' in str(e):
                    # Token expired, wait and retry
                    self._log(f"Token expired, waiting 5 seconds for auto-refresh...")
                    self.console.print("[yellow]⚠️  AWS token expired, waiting 5 seconds for auto-refresh...[/yellow]")
                    time.sleep(5)
                    # Recreate the CloudFormation client to pick up new credentials
                    self.cf_client = boto3.client('cloudformation')
                    continue  # Retry the current iteration
                else:
                    raise
                        
        # Timeout - only reached if loop completes without return
        raise Exception(f"Timeout waiting for stack {stack_name} after {timeout} seconds")
        
    def _save_progress(self, progress_file: Path, step_number: int):
        """Save installation progress for resume capability."""
        import json
        from utils import AppConfig
        
        progress_data = {
            "last_completed_step": step_number,
            "timestamp": datetime.now().isoformat(),
            "initials": AppConfig.get_developer_initials(),
            "initials_source": "override" if os.environ.get('DOCR_OVERRIDE_INITIALS') else "config"
        }
        
        with open(progress_file, 'w') as f:
            json.dump(progress_data, f, indent=2)
            
    def _log(self, message: str):
        """Append message to log file."""
        with open(self.log_file, 'a') as f:
            f.write(message + '\n')