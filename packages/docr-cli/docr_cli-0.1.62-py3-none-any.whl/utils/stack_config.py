"""
Stack and runtime configuration management.
Handles stack names, API URLs, Lambda functions, SNS topics.
"""
from typing import Dict, Any, Optional


class StackConfig:
    """Manages CloudFormation stack outputs and runtime configuration."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
    
    def get_stack_name(self, app_or_component: str = None) -> Optional[str]:
        """Get stack name for an application or component."""
        if not app_or_component:
            raise ValueError("app_or_component parameter is required")
        
        # Check applications first
        if app_or_component in self.config_data.get('applications', {}):
            return self.config_data['applications'][app_or_component].get('stack_name')
        
        # Then check components
        if app_or_component in self.config_data.get('components', {}):
            return self.config_data['components'][app_or_component].get('stack_name')
        
        # Check OIDC authorizer
        if app_or_component == 'oidc-authorizer':
            return self.config_data.get('oidc', {}).get('authorizer', {}).get('stack_name')
        
        return None
    
    def get_api_url(self, app_or_component: str = None, stage: str = "sandbox") -> Optional[str]:
        """Get API URL for an application or component for a specific stage."""
        if not app_or_component:
            raise ValueError("app_or_component parameter is required")
        
        # Map stage to the config key
        stage_key = f"stage_{stage}_api_url"
        
        # Check applications first
        if app_or_component in self.config_data.get('applications', {}):
            return self.config_data['applications'][app_or_component].get(stage_key)
        
        # Then check components
        if app_or_component in self.config_data.get('components', {}):
            return self.config_data['components'][app_or_component].get(stage_key)
        
        return None
    
    def get_lambda_function_name(self, app_or_component: str = None) -> Optional[str]:
        """Get Lambda function name for an application or component."""
        if not app_or_component:
            raise ValueError("app_or_component parameter is required")
        
        # Check applications first
        if app_or_component in self.config_data.get('applications', {}):
            return self.config_data['applications'][app_or_component].get('lambda_function_name')
        
        # Then check components
        if app_or_component in self.config_data.get('components', {}):
            return self.config_data['components'][app_or_component].get('lambda_function_name')
        
        # Check OIDC authorizer
        if app_or_component == 'oidc-authorizer':
            return self.config_data.get('oidc', {}).get('authorizer', {}).get('lambda_function_name')
        
        return None
    
    def get_sns_topic_arn(self, app_or_component: str = None) -> Optional[str]:
        """Get SNS topic ARN for an application or component."""
        if not app_or_component:
            raise ValueError("app_or_component parameter is required")
        
        # Check applications first
        if app_or_component in self.config_data.get('applications', {}):
            return self.config_data['applications'][app_or_component].get('sns_topic_arn')
        
        # Then check components
        if app_or_component in self.config_data.get('components', {}):
            return self.config_data['components'][app_or_component].get('sns_topic_arn')
        
        return None
    
    def get_component_api_url(self, component: str, stage: str = "sandbox") -> str:
        """Get the API URL for component for a specific stage."""
        component_config = self.config_data['components'].get(component, {})
        stage_key = f"stage_{stage}_api_url"
        return component_config.get(stage_key, "")
    
    def get_component_lambda_function_name(self, component: str) -> str:
        """Get Lambda function name for component."""
        component_config = self.config_data['components'].get(component, {})
        return component_config.get("lambda_function_name", "")
    
    def get_component_stack_name(self, component: str, dev_initials: str = None) -> str:
        """Get CloudFormation stack name for component."""
        component_config = self.config_data['components'].get(component, {})
        return component_config["stack_name"]
    
    def get_component_api_name(self, component: str, dev_initials: str = None) -> str:
        """Get API Gateway name for component."""
        component_config = self.config_data['components'].get(component, {})
        return component_config["api_name"]
    
    def get_credstore_config(self, app_name: str) -> dict:
        """Get credstore configuration."""
        # Get credstore product based on whether it's an app or component
        if app_name in self.config_data.get('applications', {}):
            credstore_product = self.config_data['applications'][app_name].get('credstore_product')
        elif app_name in self.config_data.get('components', {}):
            credstore_product = self.config_data['components'][app_name].get('credstore_product')
        else:
            # Fallback
            credstore_product = f"{app_name}-{self.config_data['project']['developer_initials']}"
        
        return {
            'table_name': self.config_data['credstore']['table_name'],
            'product': credstore_product,
            'dev_initials': self.config_data['project']['developer_initials']
        }