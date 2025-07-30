"""Stack verification implementation."""
import subprocess
from typing import Dict
from .base import BaseDoctorCheck
from utils import AppConfig, cloudformation_utils as CloudFormationUtils


class StackDoctor(BaseDoctorCheck):
    """Verify CloudFormation stack deployments."""
    
    def check(self) -> bool:
        """Verify all required stacks are deployed and in COMPLETE status."""
        self.console_utils.print_step(1, 1, "Checking CloudFormation stacks")
        
        config = AppConfig.load_config()
        dev_initials = AppConfig.get_developer_initials()
        
        # Get all applications and components that should have stacks
        all_apps = {}
        if 'applications' in config:
            all_apps.update(config['applications'])
        if 'components' in config:
            all_apps.update(config['components'])
            
        # Add OIDC authorizer
        if 'oidc' in config and 'authorizer' in config['oidc']:
            all_apps['oidc-authorizer'] = config['oidc']['authorizer']
        
        for app_name, app_config in all_apps.items():
            stack_name = app_config.get('stack_name')
            if not stack_name:
                self.log_result(
                    f"{app_name} stack",
                    False,
                    "No stack_name configured"
                )
                continue
                
            # Check if stack exists
            if not CloudFormationUtils.stack_exists(stack_name):
                if self.fix:
                    self.log_result(
                        f"{app_name} stack",
                        False,
                        f"Stack {stack_name} not found - deployment required",
                        fix_attempted=True
                    )
                    # Could trigger deployment here if --fix enabled
                else:
                    self.log_result(
                        f"{app_name} stack",
                        False,
                        f"Stack {stack_name} not found"
                    )
                continue
            
            # Check stack status
            try:
                stack_status = self._get_stack_status(stack_name)
                if stack_status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
                    self.log_result(
                        f"{app_name} stack",
                        True,
                        f"Status: {stack_status}"
                    )
                else:
                    self.log_result(
                        f"{app_name} stack",
                        False,
                        f"Status: {stack_status}"
                    )
            except Exception as e:
                self.log_result(
                    f"{app_name} stack",
                    False,
                    f"Error checking status: {str(e)}"
                )
        
        # Also check for stack outputs if stacks exist
        if self.verbose:
            self._check_stack_outputs(all_apps)
        
        return self.results['failed'] == 0
    
    def _get_stack_status(self, stack_name: str) -> str:
        """Get CloudFormation stack status."""
        cmd = [
            'aws', 'cloudformation', 'describe-stacks',
            '--stack-name', stack_name,
            '--query', 'Stacks[0].StackStatus',
            '--output', 'text'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    
    def _check_stack_outputs(self, all_apps: Dict[str, Dict]) -> None:
        """Check stack outputs for completeness (verbose mode only)."""
        self.console_utils.print_info("\n  Stack outputs check:")
        
        for app_name, app_config in all_apps.items():
            stack_name = app_config.get('stack_name')
            if not stack_name:
                continue
                
            if CloudFormationUtils.stack_exists(stack_name):
                outputs = CloudFormationUtils.get_stack_outputs(stack_name)
                if outputs:
                    output_keys = ', '.join(outputs.keys())
                    self.console_utils.print_info(f"    {app_name}: {len(outputs)} outputs ({output_keys})")
                else:
                    self.console_utils.print_warning(f"    {app_name}: No outputs found")