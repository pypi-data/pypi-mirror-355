#!/usr/bin/env python3
"""
API Gateway utilities for getting API IDs from configuration.
"""
from typing import Dict, Optional
from urllib.parse import urlparse

from .app_config import AppConfig


class APIGatewayUtils:
    """Utilities for working with API Gateway IDs from configuration."""
    
    @staticmethod
    def extract_api_id_from_url(api_url: str) -> Optional[str]:
        """
        Extract API Gateway ID from an API URL.
        
        Args:
            api_url: Full API URL (e.g., https://4hfd40sch0.execute-api.us-east-1.amazonaws.com/)
            
        Returns:
            API Gateway ID (e.g., '4hfd40sch0') or None if extraction fails
        """
        if not api_url:
            return None
            
        try:
            # Parse the URL
            parsed = urlparse(api_url)
            hostname = parsed.hostname
            
            if hostname and '.execute-api.' in hostname:
                # Extract the API ID (first part of hostname)
                api_id = hostname.split('.')[0]
                return api_id
        except Exception:
            pass
            
        return None
    
    @staticmethod
    def get_all_api_gateway_ids(stage: str = "sandbox") -> Dict[str, str]:
        """
        Get all API Gateway IDs from TOML configuration.
        
        Args:
            stage: Environment stage (sandbox, dev, qa, prod)
            
        Returns:
            Dictionary mapping app/component names to their API Gateway IDs
        """
        api_gateway_ids = {}
        
        # Get API IDs from applications
        for app_name in AppConfig.discover_applications():
            api_url = AppConfig.get_api_url(app_name, stage)
            if api_url:
                api_id = APIGatewayUtils.extract_api_id_from_url(api_url)
                if api_id:
                    api_gateway_ids[app_name] = api_id
        
        # Get API IDs from components
        for comp_name in AppConfig.discover_components():
            # get_component_api_url is on StackConfig, not AppConfig
            from .stack_config import StackConfig
            stack_config = StackConfig(AppConfig.load_config())
            api_url = stack_config.get_component_api_url(comp_name, stage)
            if api_url:
                api_id = APIGatewayUtils.extract_api_id_from_url(api_url)
                if api_id:
                    api_gateway_ids[comp_name] = api_id
        
        # Special handling for oidc (maps to oidc-manager)
        if 'oidc-manager' in api_gateway_ids:
            api_gateway_ids['oidc'] = api_gateway_ids['oidc-manager']
        
        return api_gateway_ids
    
    @staticmethod
    def validate_required_apis(api_gateway_ids: Dict[str, str], required_apis: list) -> list:
        """
        Validate that all required APIs are present.
        
        Args:
            api_gateway_ids: Dictionary of discovered API Gateway IDs
            required_apis: List of required API names
            
        Returns:
            List of missing API names (empty if all present)
        """
        return [api for api in required_apis if api not in api_gateway_ids or not api_gateway_ids[api]]