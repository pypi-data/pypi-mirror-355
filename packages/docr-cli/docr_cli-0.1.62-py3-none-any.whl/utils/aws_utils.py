#!/usr/bin/env python3
"""
AWS utilities for CLI scripts.
Provides API Gateway discovery, token validation, and AWS service helpers.
"""
import boto3
from typing import Dict, Optional
from rich.table import Table
from rich.console import Console

from .config_utils import ConfigUtils


class AWSUtils:
    """AWS utility functions."""
    
    @staticmethod
    def discover_api_gateway_ids(stage: str = "sandbox", verify_mode: bool = False) -> Dict[str, str]:
        """
        Discover API Gateway IDs using boto3 based on naming patterns.
        
        Note: Only legislative-review has a frontend config file. Component apps 
        (cost, jobs, workspaces) are embeddable React components that only need 
        API registration, not frontend configs.
        
        Args:
            stage: Environment stage (sandbox, dev, etc.)
            verify_mode: If True, prints a verification table
            
        Returns:
            Dictionary mapping app names to API Gateway IDs
        """
        console = Console()
        
        # Get developer initials from TOML config
        try:
            from .app_config import AppConfig
            dev_initials = AppConfig.get_developer_initials()
        except Exception as e:
            if verify_mode:
                console.print(f"  ❌ Failed to load config: {e}")
                return {}
            else:
                raise RuntimeError(f"Failed to load config for API discovery: {e}")
        
        # Expected naming patterns
        from .app_config import AppConfig
        
        # Build API patterns dynamically from component metadata
        api_patterns = {
            comp: AppConfig.get_component_api_name(comp)
            for comp in AppConfig.discover_components()
        }
        
        # Add ALL applications, not just active one
        all_applications = AppConfig.discover_applications()
        for app_name in all_applications:
            api_patterns[app_name] = f"{app_name}-{dev_initials}-"  # Has random suffix
            
        # Add oidc pattern (maps to oidc-manager application)
        api_patterns["oidc"] = f"oidc-app-backend-{dev_initials}-api"
        
        discovered_apis = {}
        
        try:
            # Use boto3 to list all API Gateway v2 (HTTP APIs)
            apigatewayv2 = boto3.client('apigatewayv2', region_name='us-east-1')
            response = apigatewayv2.get_apis(MaxResults='500')  # Get all v2 APIs with higher limit
            
            # Filter APIs that contain our developer initials
            candidate_apis = []
            for api in response.get('Items', []):
                api_name = api.get('Name', '')
                if f"-{dev_initials}-" in api_name:
                    candidate_apis.append({
                        'id': api['ApiId'],
                        'name': api_name,
                        'description': api.get('Description', '')
                    })
            
            # Match APIs to our expected patterns
            for app_name, pattern in api_patterns.items():
                matches = []
                
                for api in candidate_apis:
                    from .app_config import AppConfig
                    if AppConfig.is_application(app_name):
                        # Application has random suffix
                        if api['name'].startswith(pattern):
                            matches.append(api)
                    else:
                        # Exact match for component apps
                        if api['name'] == pattern:
                            matches.append(api)
                
                if len(matches) == 0:
                    if verify_mode:
                        console.print(f"  ❌ No API found for {app_name} (pattern: {pattern})")
                elif len(matches) == 1:
                    discovered_apis[app_name] = matches[0]['id']
                    if verify_mode:
                        console.print(f"  ✅ Found {app_name} API: {matches[0]['id']} ({matches[0]['name']})")
                else:
                    # Error: multiple matches for same prefix
                    if verify_mode:
                        console.print(f"  ❌ Multiple APIs found for {app_name} (pattern: {pattern}):")
                        for match in matches:
                            console.print(f"      - {match['id']}: {match['name']}")
                    else:
                        raise ValueError(f"Multiple API matches for {app_name}: {[m['name'] for m in matches]}")
            
            if verify_mode:
                # Print summary table
                table = Table(title=f"API Gateway Discovery - {dev_initials} ({stage})")
                table.add_column("Application", style="cyan")
                table.add_column("Pattern", style="dim")
                table.add_column("Status", style="bold")
                table.add_column("API Gateway ID", style="green")
                
                for app_name, pattern in api_patterns.items():
                    if app_name in discovered_apis:
                        table.add_row(
                            app_name,
                            pattern,
                            "✅ Found",
                            discovered_apis[app_name]
                        )
                    else:
                        table.add_row(
                            app_name,
                            pattern, 
                            "❌ Missing",
                            "Not found"
                        )
                
                console.print(table)
                console.print(f"\nFound {len(discovered_apis)}/{len(api_patterns)} expected APIs")
            
            return discovered_apis
            
        except Exception as e:
            if verify_mode:
                console.print(f"  ❌ API Gateway discovery failed: {e}")
                return {}
            else:
                raise RuntimeError(f"Failed to discover API Gateway IDs: {e}")
    
    @staticmethod
    def verify_aws_token() -> tuple[bool, str]:
        """
        Verify AWS token is valid and not expired.
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Try a simple AWS operation to verify credentials
            sts = boto3.client('sts')
            response = sts.get_caller_identity()
            
            # If we get here, credentials are valid
            account_id = response.get('Account', 'Unknown')
            user_arn = response.get('Arn', 'Unknown')
            
            return True, f"AWS credentials valid - Account: {account_id}, User: {user_arn}"
            
        except boto3.exceptions.Boto3Error as e:
            return False, f"❌ AWS credentials invalid or expired: {e}"
        except Exception as e:
            return False, f"❌ Failed to verify AWS credentials: {e}"
    
