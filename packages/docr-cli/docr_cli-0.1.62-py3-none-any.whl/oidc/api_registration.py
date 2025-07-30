"""
API Registration
- Register OIDC client with all discovered APIs
- Handle Node.js script execution for API registration
"""
import os
from typing import Dict, List
from rich.console import Console
from utils import AWSUtils, ConsoleUtils, CommandUtils, OIDCConfigManager, APIGatewayUtils
from utils.shared_console import get_shared_console


class ApiRegistrationStep:
    """Handle API Gateway registration for OIDC clients."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def _get_allowed_clients_for_api(self, api_name: str, app_name: str, app_client_mapping: Dict[str, str], current_client_id: str = None) -> List[str]:
        """Determine which client IDs should be allowed for a specific API.
        
        Based on the reference pattern:
        - Each app's API only allows its own client
        - Component APIs (cost, jobs, workspaces) allow the legislative-review client
        
        Args:
            api_name: Name of the API 
            app_name: Name of the app currently being registered
            app_client_mapping: Mapping of app names to their client IDs
            current_client_id: The client ID currently being registered
        """
        # Normalize API names by removing suffixes
        api_base = api_name.lower().replace('-api', '').replace('_api', '')
        
        # OIDC Manager API only allows OIDC Manager client
        if api_base in ['oidc', 'oidc-manager', 'oidcmanager']:
            # If we're registering oidc-manager, use the current client ID
            if app_name == 'oidc-manager' and current_client_id:
                return [current_client_id]
            # Otherwise use the mapped client
            return [app_client_mapping.get('oidc-manager', '')] if 'oidc-manager' in app_client_mapping else []
        
        # Component APIs allow legislative-review client
        if api_base in ['cost', 'costs', 'job', 'jobs', 'workspace', 'workspaces']:
            # If we're registering legislative-review, use the current client ID
            if app_name == 'legislative-review' and current_client_id:
                return [current_client_id]
            # Otherwise use the mapped client
            return [app_client_mapping.get('legislative-review', '')] if 'legislative-review' in app_client_mapping else []
        
        # Legislative Review API allows legislative-review client
        if api_base in ['legislative-review', 'legislativereview', 'legislative', 'leg-review']:
            # If we're registering legislative-review, use the current client ID
            if app_name == 'legislative-review' and current_client_id:
                return [current_client_id]
            # Otherwise use the mapped client
            return [app_client_mapping.get('legislative-review', '')] if 'legislative-review' in app_client_mapping else []
        
        # Default: if we can't determine, return empty list
        return []
    
    def register_with_all_apis(self, client_id: str, stage: str, dev_initials: str, discovered_apis: Dict[str, str], app_name: str = None) -> List[str]:
        """Update all APIs with their correct allowed clients.
        
        This method is called during each app registration, but we need to ensure
        all APIs have the correct allowed clients based on the reference pattern.
        """
        # Get OIDC scripts directory using consolidated utility
        try:
            oidc_scripts_dir = OIDCConfigManager.get_oidc_scripts_dir()
        except RuntimeError as e:
            self.console.print(f"  ⚠ {e}")
            return []
        
        try:
            resource_table_name = OIDCConfigManager.get_oidc_table_name(dev_initials)
            aws_region = "us-east-1"
            
            # Use provided discovered APIs or get them from TOML config
            if not discovered_apis:
                self.console.print("  → Getting API Gateway IDs from configuration...")
                discovered_apis = APIGatewayUtils.get_all_api_gateway_ids(stage)
                
                # Validate we have all required APIs
                required_apis = ['legislative-review', 'workspaces', 'costs', 'jobs']
                missing_apis = APIGatewayUtils.validate_required_apis(discovered_apis, required_apis)
                
                if missing_apis:
                    self.console_utils.print_error(
                        f"Missing required API Gateway configurations: {', '.join(missing_apis)}\n\n"
                        f"Please ensure all components are deployed and run 'docr refresh' to update configuration.",
                        exit_code=1
                    )
            
            # Get all registered application clients from DynamoDB
            from boto3 import client as boto3_client
            dynamodb = boto3_client('dynamodb', region_name=aws_region)
            
            # Query for all clients
            response = dynamodb.scan(
                TableName=resource_table_name,
                FilterExpression='PK = :pk AND begins_with(SK, :sk)',
                ExpressionAttributeValues={
                    ':pk': {'S': 'ORG#UMD#CLIENT'},
                    ':sk': {'S': 'CLIENT#'}
                }
            )
            
            # Build mapping of app names to client IDs
            app_client_mapping = {}
            for item in response.get('Items', []):
                redirect_uri = item.get('redirectUri', {}).get('S', '')
                client_sk = item.get('SK', {}).get('S', '')
                
                if redirect_uri and client_sk:
                    # Extract client ID from SK
                    client_id_from_sk = client_sk.replace('CLIENT#', '')
                    
                    # Extract app name from redirect URI
                    # Format: https://app-name-dev.it-eng-ai.aws.umd.edu/
                    if 'legislative-review' in redirect_uri:
                        app_client_mapping['legislative-review'] = client_id_from_sk
                    elif 'oidc-manager' in redirect_uri:
                        app_client_mapping['oidc-manager'] = client_id_from_sk
            
            # Add the current client being registered
            if app_name and client_id:
                app_client_mapping[app_name] = client_id
            
            add_api_script = oidc_scripts_dir / "add-api-clients.js"
            registered_apis = []
            
            # Update each API with its correct allowed clients
            for api_name, api_gateway_id in discovered_apis.items():
                try:
                    # Determine which clients should be allowed for this API
                    allowed_clients = self._get_allowed_clients_for_api(api_name, app_name, app_client_mapping, client_id)
                    
                    if not allowed_clients or not any(allowed_clients):
                        self.console.print(f"  ⚠ Skipping {api_name} API - no valid clients to register")
                        continue
                    
                    # Filter out empty strings
                    allowed_clients = [c for c in allowed_clients if c]
                    
                    self.console.print(f"  → Registering with {api_name} API ({api_gateway_id})")
                    
                    cmd = [
                        "node", str(add_api_script),
                        "--api", api_gateway_id,
                        "--name", f"{api_name} API",
                        "--clients", ','.join(allowed_clients),
                        "--table", resource_table_name
                    ]
                    
                    env = os.environ.copy()
                    env["AWS_REGION"] = aws_region
                    
                    # Use CommandUtils instead of raw subprocess
                    success, output = CommandUtils.run_command(
                        cmd, 
                        shell=False, 
                        check=False, 
                        capture_output=True, 
                        cwd=oidc_scripts_dir, 
                        env=env
                    )
                    
                    if success:
                        self.console.print(f"    ✓ {api_name} API registration successful")
                        registered_apis.append(api_name)
                    else:
                        self.console.print(f"    ⚠ {api_name} API registration failed: {output}")
                except Exception as e:
                    self.console.print(f"    ⚠ {api_name} API registration error: {e}")
            
            if registered_apis:
                self.console.print(f"  ✓ Client registered with {len(registered_apis)} APIs: {', '.join(registered_apis)}")
            else:
                self.console.print(f"  ⚠ No APIs were successfully registered")
            
            return registered_apis
                    
        except Exception as e:
            self.console.print(f"  ⚠ API registration failed: {e}")
            return []