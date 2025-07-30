"""Utility functions for the installation process."""

import json
import subprocess
from typing import Optional
from pathlib import Path
from datetime import datetime
from rich.table import Table
from rich import box
from utils import AppConfig
from utils.shared_console import get_shared_console


def check_setup_complete() -> bool:
    """Check if setup has been completed by verifying TOML file exists with initials."""
    try:
        # Check if TOML config file exists
        config_file = AppConfig.CONFIG_FILE
        if not config_file.exists():
            return False
        
        # Check if initials are configured
        initials = AppConfig.get_developer_initials()
        if not initials:
            return False
            
        return True
    except Exception:
        return False


def setup_logging(log_dir: Path) -> Path:
    """Setup logging directory and file."""
    import os
    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Create timestamped log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"install_{timestamp}.log"
    
    # Write initial log entry
    with open(log_file, 'w') as f:
        f.write(f"Document Review System Installation Log\n")
        f.write(f"Started at: {datetime.now().isoformat()}\n")
        f.write(f"Initials: {AppConfig.get_developer_initials()}\n")
        f.write(f"Initials Source: {'override' if os.environ.get('DOCR_OVERRIDE_INITIALS') else 'config'}\n")
        f.write(f"{'='*80}\n\n")
        
    return log_file


def load_progress(progress_file: Path) -> Optional[int]:
    """Load saved progress if available."""
    if progress_file.exists():
        with open(progress_file) as f:
            data = json.load(f)
            return data.get("last_completed_step")
    return None


def filter_stacks(initials: str, log_callback=None):
    """Filter and display stacks for the current initials."""
    console = get_shared_console()
    
    try:
        cmd = [
            'aws', 'cloudformation', 'list-stacks',
            '--stack-status-filter', 'CREATE_COMPLETE', 'UPDATE_COMPLETE',
            '--output', 'json'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Handle token expiry
        if result.returncode != 0 and 'ExpiredToken' in result.stderr:
            if log_callback:
                log_callback("Token expired in final verification, waiting 5 seconds for auto-refresh...")
            console.print("[yellow]⚠️  AWS token expired, waiting 5 seconds for auto-refresh...[/yellow]")
            import time
            time.sleep(5)
            # Retry once
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            stacks_data = json.loads(result.stdout)
            user_stacks = []
            
            for stack in stacks_data.get('StackSummaries', []):
                if initials in stack['StackName']:
                    user_stacks.append(stack['StackName'])
            
            if user_stacks:
                table = Table(title="Deployed Stacks", box=box.SIMPLE)
                table.add_column("Stack Name", style="cyan")
                
                for stack in sorted(user_stacks):
                    table.add_row(stack)
                
                console.print("\n")
                console.print(table)
                if log_callback:
                    log_callback(f"\nDeployed stacks: {', '.join(sorted(user_stacks))}")
    except Exception as e:
        if log_callback:
            log_callback(f"Error filtering stacks: {str(e)}")