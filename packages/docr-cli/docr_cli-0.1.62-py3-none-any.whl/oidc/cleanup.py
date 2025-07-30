"""
Cleanup Operations
- Clean up old OIDC registrations
- Remove old client configurations from DynamoDB
"""
from typing import Dict
from utils import AWSUtils, ConsoleUtils, OIDCConfigManager, DynamoDBUtils, APIGatewayUtils
from utils.shared_console import get_shared_console


class CleanupStep:
    """Handle cleanup of old OIDC registrations."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def cleanup_all_previous_registrations(self, stage: str, discovered_apis: Dict[str, str]):
        """Clean up ALL previous OIDC registrations for all apps - used once at start of register all."""
        try:
            # Get configuration using consolidated utility
            config, dev_initials = OIDCConfigManager.get_oidc_config(stage)
            
            # Use discovered APIs or get them from TOML config
            if not discovered_apis:
                discovered_apis = APIGatewayUtils.get_all_api_gateway_ids(stage)
            
            # Get DynamoDB client and table using consolidated utility
            dynamodb, table_name = DynamoDBUtils.get_oidc_client_and_table(dev_initials)
            
            old_clients_removed = []
            old_client_configs_removed = []
            
            # Step 1: Find ALL old clients using consolidated utility
            # Get all applications and components dynamically
            from utils import AppConfig
            applications = AppConfig.discover_applications()
            components = AppConfig.discover_components()
            apps = applications + components
            old_client_ids = DynamoDBUtils.get_client_ids_for_apps(dynamodb, table_name, apps, dev_initials)
            
            # Step 2: Remove old clients from all API allowed lists using consolidated utility
            for api_name, api_id in discovered_apis.items():
                try:
                    removed_clients = DynamoDBUtils.remove_clients_from_api(dynamodb, table_name, api_id, old_client_ids)
                    for client_id in removed_clients:
                        old_clients_removed.append((api_name, client_id))
                except Exception as e:
                    self.console.print(f"  ⚠ Could not clean up {api_name} API: {e}")
            
            # Step 3: Remove old client configurations from DynamoDB using consolidated utility
            for client_id in old_client_ids:
                try:
                    DynamoDBUtils.delete_client_configuration(dynamodb, table_name, client_id)
                    old_client_configs_removed.append(client_id)
                except Exception as e:
                    self.console.print(f"  ⚠ Could not remove client config {client_id}: {e}")
            
            # Report cleanup results
            total_removed = len(old_clients_removed) + len(old_client_configs_removed)
            if total_removed > 0:
                self.console.print(f"  ✓ Cleaned up {len(set(old_client_ids))} old client registrations for all apps")
                for api_name, client_id in old_clients_removed:
                    self.console.print(f"    - Removed {client_id} from {api_name} API")
                for client_id in old_client_configs_removed:
                    self.console.print(f"    - Removed client configuration {client_id}")
            else:
                self.console.print("  ✓ No previous registrations to clean up")
                
        except Exception as e:
            self.console.print(f"  ⚠ Global cleanup failed: {e}")
            self.console.print("  → Continuing with registration...")