#!/usr/bin/env python3
"""
CloudFormation utilities for stack operations.
"""
import subprocess
import json
from typing import Dict, Optional, Tuple


def get_stack_outputs(
    stack_name: str,
    fail_on_error: bool = False,
    console_utils: Optional[object] = None
) -> Dict[str, str]:
    """
    Get CloudFormation stack outputs.
    
    Args:
        stack_name: Name of the CloudFormation stack
        fail_on_error: If True, exit on error. If False, return empty dict on error
        console_utils: Console utilities instance for error messages (required if fail_on_error=True)
        
    Returns:
        Dictionary of output key-value pairs, or empty dict if error and fail_on_error=False
        
    Raises:
        SystemExit: If fail_on_error=True and an error occurs
    """
    cmd = [
        'aws', 'cloudformation', 'describe-stacks',
        '--no-cli-pager', '--stack-name', stack_name,
        '--query', 'Stacks[0].Outputs', '--output', 'json'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Handle null or empty response
        if result.stdout.strip() == 'null' or not result.stdout.strip():
            if fail_on_error and console_utils:
                console_utils.print_error(
                    f"Stack '{stack_name}' has no outputs",
                    exit_code=1
                )
            return {}
        
        outputs = json.loads(result.stdout)
        if not outputs:
            return {}
            
        return {output['OutputKey']: output['OutputValue'] for output in outputs}
        
    except subprocess.CalledProcessError as e:
        # Stack doesn't exist or other AWS CLI error
        if fail_on_error and console_utils:
            error_msg = e.stderr if e.stderr else str(e)
            console_utils.print_error(
                f"Failed to get stack outputs for '{stack_name}': {error_msg}",
                exit_code=1
            )
        return {}
        
    except (json.JSONDecodeError, TypeError) as e:
        if fail_on_error and console_utils:
            console_utils.print_error(
                f"Failed to parse stack outputs for '{stack_name}': {str(e)}",
                exit_code=1
            )
        return {}


def stack_exists(stack_name: str) -> bool:
    """
    Check if a CloudFormation stack exists.
    
    Args:
        stack_name: Name of the CloudFormation stack
        
    Returns:
        True if stack exists, False otherwise
    """
    cmd = [
        'aws', 'cloudformation', 'describe-stacks',
        '--no-cli-pager', '--stack-name', stack_name,
        '--query', 'Stacks[0].StackName', '--output', 'text'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip() == stack_name
    except subprocess.CalledProcessError:
        return False


def get_stack_output_value(stack_name: str, output_key: str) -> Optional[str]:
    """
    Get a specific output value from a CloudFormation stack.
    
    Args:
        stack_name: Name of the CloudFormation stack
        output_key: The output key to retrieve
        
    Returns:
        The output value if found, None otherwise
    """
    outputs = get_stack_outputs(stack_name, fail_on_error=False)
    return outputs.get(output_key)