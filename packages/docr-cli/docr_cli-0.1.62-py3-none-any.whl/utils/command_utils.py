#!/usr/bin/env python3
"""
Shell command execution utilities for CLI scripts.
Provides consistent command execution and error handling.
"""
import subprocess
import shutil
from typing import Optional, Union, List
from pathlib import Path


class CommandUtils:
    """Shell command execution utilities."""
    
    @staticmethod
    def run_command(
        cmd: Union[str, List[str]], 
        shell: bool = None, 
        check: bool = True, 
        capture_output: bool = True,
        cwd: Optional[Path] = None,
        env: Optional[dict] = None
    ) -> tuple[bool, str]:
        """
        Run shell command with standard error handling.
        
        Args:
            cmd: Command to run (string for shell=True, list for shell=False)
            shell: Whether to run through shell (auto-detected if None)
            check: Whether to raise exception on non-zero exit
            capture_output: Whether to capture stdout/stderr
            cwd: Working directory for command
            env: Environment variables
            
        Returns:
            Tuple of (success, output) where output is stdout or error message
        """
        # Auto-detect shell mode if not specified
        if shell is None:
            shell = isinstance(cmd, str)
        
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                check=check,
                capture_output=capture_output,
                text=True,
                cwd=cwd,
                env=env
            )
            output = result.stdout if capture_output else ""
            return True, output.strip()
        except subprocess.CalledProcessError as e:
            # Combine stderr and stdout for error message
            error_output = ""
            if e.stderr:
                error_output = e.stderr
            elif e.stdout:
                error_output = e.stdout
            else:
                error_output = f"Command failed with exit code {e.returncode}"
            
            if not check:
                return False, error_output.strip()
            
            # Re-raise if check=True
            raise
    
    @staticmethod
    def run_shell_command(
        cmd: str,
        capture_output: bool = True,
        cwd: Optional[Path] = None,
        env: Optional[dict] = None
    ) -> tuple[bool, str]:
        """
        Run a shell command string.
        
        Args:
            cmd: Shell command string
            capture_output: Whether to capture output
            cwd: Working directory
            env: Environment variables
            
        Returns:
            Tuple of (success, output)
        """
        return CommandUtils.run_command(
            cmd=cmd,
            shell=True,
            check=False,
            capture_output=capture_output,
            cwd=cwd,
            env=env
        )
    
    @staticmethod
    def check_command_exists(cmd: str) -> bool:
        """
        Check if a command exists in PATH.
        
        Args:
            cmd: Command name to check
            
        Returns:
            True if command exists, False otherwise
        """
        return shutil.which(cmd) is not None
    
    @staticmethod
    def run_aws_command(
        service: str,
        operation: str,
        parameters: Optional[List[str]] = None,
        query: Optional[str] = None,
        output: str = "json"
    ) -> subprocess.CompletedProcess:
        """
        Run AWS CLI command with consistent formatting.
        
        Args:
            service: AWS service (e.g., 'lambda', 'cloudformation')
            operation: Operation to perform
            parameters: Additional parameters
            query: JMESPath query for output
            output: Output format (json, text, table)
            
        Returns:
            Command result
        """
        cmd_parts = ["aws", service, operation, "--no-cli-pager"]
        
        if parameters:
            cmd_parts.extend(parameters)
        
        if query:
            cmd_parts.extend(["--query", query])
        
        cmd_parts.extend(["--output", output])
        
        return CommandUtils.run_command(cmd_parts, shell=False)
    
    @staticmethod
    def get_command_output(
        cmd: Union[str, List[str]], 
        default: str = "",
        shell: bool = True
    ) -> str:
        """
        Get command output as string, with default on failure.
        
        Args:
            cmd: Command to run
            default: Default value if command fails
            shell: Whether to run through shell
            
        Returns:
            Command output or default value
        """
        try:
            result = CommandUtils.run_command(
                cmd, 
                shell=shell, 
                check=True, 
                capture_output=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return default
    
    @staticmethod
    def run_docker_command(
        operation: str,
        args: Optional[List[str]] = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run Docker command with consistent formatting.
        
        Args:
            operation: Docker operation (e.g., 'build', 'push')
            args: Additional arguments
            check: Whether to raise on error
            
        Returns:
            Command result
        """
        cmd_parts = ["docker", operation]
        if args:
            cmd_parts.extend(args)
        
        return CommandUtils.run_command(cmd_parts, shell=False, check=check)
    
    @staticmethod
    def run_sam_command(
        operation: str,
        args: Optional[List[str]] = None,
        check: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run SAM CLI command.
        
        Args:
            operation: SAM operation (e.g., 'build', 'deploy')
            args: Additional arguments
            check: Whether to raise on error
            
        Returns:
            Command result
        """
        cmd_parts = ["sam", operation]
        if args:
            cmd_parts.extend(args)
        
        return CommandUtils.run_command(cmd_parts, shell=False, check=check)
    
    @staticmethod
    def check_aws_credentials() -> bool:
        """
        Check if AWS credentials are configured.
        
        Returns:
            True if credentials are valid
        """
        try:
            result = CommandUtils.run_aws_command(
                "sts", 
                "get-caller-identity",
                output="text"
            )
            return result.returncode == 0
        except:
            return False
    
    @staticmethod
    def get_aws_account_id() -> Optional[str]:
        """
        Get current AWS account ID.
        
        Returns:
            Account ID or None if not available
        """
        try:
            result = CommandUtils.run_aws_command(
                "sts",
                "get-caller-identity",
                query="Account",
                output="text"
            )
            return result.stdout.strip()
        except:
            return None
    
    @staticmethod
    def get_aws_region() -> Optional[str]:
        """
        Get current AWS region.
        
        Returns:
            Region or None if not configured
        """
        import os
        
        # Check environment variable first
        region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION')
        if region:
            return region
        
        # Try AWS CLI config
        try:
            result = CommandUtils.run_command(
                "aws configure get region",
                shell=True,
                check=False
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except:
            pass
        
        return None
    
    @staticmethod
    def run_with_progress(
        cmd: Union[str, List[str]],
        description: str = "Running command...",
        shell: bool = True
    ) -> subprocess.CompletedProcess:
        """
        Run command with a progress indicator.
        
        Args:
            cmd: Command to run
            description: Description for progress
            shell: Whether to run through shell
            
        Returns:
            Command result
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task(description, total=None)
            result = CommandUtils.run_command(cmd, shell=shell)
            progress.update(task, completed=True)
            
        return result