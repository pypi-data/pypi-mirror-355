"""Cleanup operations implementation."""
import re
from typing import Set, List
from .base import BaseDoctorCheck
from utils import AppConfig
from utils.dynamodb_utils import DynamoDBUtils
from utils.umd_credential_store import get_credential, delete_credential


class CleanupDoctor(BaseDoctorCheck):
    """Clean up orphaned resources and invalid configurations."""
    
    def check(self) -> bool:
        """Perform cleanup operations."""
        self.console_utils.print_step(1, 3, "Cleaning orphaned OIDC clients")
        self._cleanup_orphaned_oidc_clients()
        
        self.console_utils.print_step(2, 3, "Cleaning invalid API registrations")
        self._cleanup_invalid_api_registrations()
        
        self.console_utils.print_step(3, 3, "Cleaning credential store entries")
        self._cleanup_credential_store()
        
        return True  # Cleanup always "succeeds"
    
    def _cleanup_orphaned_oidc_clients(self):
        """Remove OIDC clients that don't correspond to current apps."""
        try:
            dev_initials = AppConfig.get_developer_initials()
            dynamodb, table_name = DynamoDBUtils.get_oidc_client_and_table(dev_initials)
            
            # Get current valid apps
            config = AppConfig.load_config()
            valid_apps = set()
            
            if 'applications' in config:
                valid_apps.update(config['applications'].keys())
            
            # Build expected client patterns
            expected_patterns = set()
            for app in valid_apps:
                # Client IDs follow pattern: {app}-{dev_initials}
                expected_patterns.add(f"{app}-{dev_initials}")
            
            if self.verbose:
                self.console_utils.print_info(f"  Expected client patterns: {', '.join(expected_patterns)}")
            
            # Scan for all clients in DynamoDB
            try:
                response = dynamodb.scan(
                    TableName=table_name,
                    FilterExpression='entity_type = :entity_type',
                    ExpressionAttributeValues={
                        ':entity_type': {'S': 'CLIENT'}
                    }
                )
                
                items = response.get('Items', [])
                orphaned_count = 0
                
                for item in items:
                    client_id = item.get('PK', {}).get('S', '').replace('CLIENT#', '')
                    
                    # Check if this client matches any expected pattern
                    is_valid = False
                    for pattern in expected_patterns:
                        if client_id == pattern or client_id.startswith(f"{pattern}-"):
                            is_valid = True
                            break
                    
                    if not is_valid and client_id:
                        orphaned_count += 1
                        if self.verbose:
                            self.console_utils.print_warning(f"    Found orphaned client: {client_id}")
                        
                        if self.fix:
                            # Delete the orphaned client
                            try:
                                dynamodb.delete_item(
                                    TableName=table_name,
                                    Key={
                                        'PK': {'S': f'CLIENT#{client_id}'},
                                        'SK': {'S': 'METADATA'}
                                    }
                                )
                                self.console_utils.print_info(f"    Deleted orphaned client: {client_id}")
                            except Exception as e:
                                self.console_utils.print_error(f"    Failed to delete {client_id}: {str(e)}")
                
                if orphaned_count > 0:
                    if self.fix:
                        self.log_result(
                            "Orphaned OIDC clients",
                            True,
                            f"Cleaned up {orphaned_count} orphaned clients",
                            fix_attempted=True
                        )
                    else:
                        self.log_result(
                            "Orphaned OIDC clients",
                            False,
                            f"Found {orphaned_count} orphaned clients (use --fix to clean)"
                        )
                else:
                    self.log_result(
                        "Orphaned OIDC clients",
                        True,
                        "No orphaned clients found"
                    )
                    
            except Exception as e:
                self.log_result(
                    "Orphaned OIDC clients scan",
                    False,
                    f"Failed to scan DynamoDB: {str(e)}"
                )
                
        except Exception as e:
            self.log_result(
                "Orphaned OIDC clients",
                False,
                f"Cleanup failed: {str(e)}"
            )
    
    def _cleanup_invalid_api_registrations(self):
        """Remove API registrations for non-existent APIs."""
        try:
            dev_initials = AppConfig.get_developer_initials()
            dynamodb, table_name = DynamoDBUtils.get_oidc_client_and_table(dev_initials)
            
            # Get current valid API IDs
            from utils.api_gateway_utils import APIGatewayUtils
            try:
                valid_apis = APIGatewayUtils.get_all_api_gateway_ids(self.stage)
                valid_api_ids = set(valid_apis.values())
                
                if self.verbose:
                    self.console_utils.print_info(f"  Found {len(valid_api_ids)} valid APIs")
            except Exception as e:
                self.console_utils.print_warning(f"  Could not get valid APIs: {str(e)}")
                valid_api_ids = set()
            
            # Scan for API registrations
            try:
                response = dynamodb.scan(
                    TableName=table_name,
                    FilterExpression='begins_with(PK, :prefix)',
                    ExpressionAttributeValues={
                        ':prefix': {'S': 'API#'}
                    }
                )
                
                items = response.get('Items', [])
                invalid_count = 0
                
                for item in items:
                    api_id = item.get('PK', {}).get('S', '').replace('API#', '')
                    
                    if api_id and api_id not in valid_api_ids:
                        invalid_count += 1
                        if self.verbose:
                            self.console_utils.print_warning(f"    Found registration for non-existent API: {api_id}")
                        
                        if self.fix:
                            # Delete all registrations for this API
                            try:
                                # Need to query for all items with this API ID
                                api_response = dynamodb.query(
                                    TableName=table_name,
                                    KeyConditionExpression='PK = :pk',
                                    ExpressionAttributeValues={
                                        ':pk': {'S': f'API#{api_id}'}
                                    }
                                )
                                
                                for api_item in api_response.get('Items', []):
                                    dynamodb.delete_item(
                                        TableName=table_name,
                                        Key={
                                            'PK': api_item['PK'],
                                            'SK': api_item['SK']
                                        }
                                    )
                                
                                self.console_utils.print_info(f"    Cleaned registrations for API: {api_id}")
                            except Exception as e:
                                self.console_utils.print_error(f"    Failed to clean API {api_id}: {str(e)}")
                
                if invalid_count > 0:
                    if self.fix:
                        self.log_result(
                            "Invalid API registrations",
                            True,
                            f"Cleaned up {invalid_count} invalid API registrations",
                            fix_attempted=True
                        )
                    else:
                        self.log_result(
                            "Invalid API registrations",
                            False,
                            f"Found {invalid_count} invalid API registrations (use --fix to clean)"
                        )
                else:
                    self.log_result(
                        "Invalid API registrations",
                        True,
                        "No invalid API registrations found"
                    )
                    
            except Exception as e:
                self.log_result(
                    "Invalid API registrations scan",
                    False,
                    f"Failed to scan for API registrations: {str(e)}"
                )
                
        except Exception as e:
            self.log_result(
                "Invalid API registrations",
                False,
                f"Cleanup failed: {str(e)}"
            )
    
    def _cleanup_credential_store(self):
        """Remove unused credential store entries."""
        try:
            config = AppConfig.load_config()
            
            # Get all expected secret keys
            expected_keys = set()
            
            # Add application secret keys
            if 'applications' in config:
                for app_name, app_config in config['applications'].items():
                    if 'secret_key' in app_config:
                        expected_keys.add(app_config['secret_key'])
            
            # Add component secret keys (though components typically don't have secrets)
            if 'components' in config:
                for comp_name, comp_config in config['components'].items():
                    if 'secret_key' in comp_config:
                        expected_keys.add(comp_config['secret_key'])
            
            if self.verbose:
                self.console_utils.print_info(f"  Expected credential keys: {', '.join(expected_keys)}")
            
            # Note: We can't easily list all keys in credential store
            # So we'll just verify expected keys exist
            missing_keys = []
            for key in expected_keys:
                try:
                    value = get_credential(key)
                    if not value:
                        missing_keys.append(key)
                except Exception:
                    missing_keys.append(key)
            
            if missing_keys:
                self.log_result(
                    "Credential store entries",
                    False,
                    f"Missing expected keys: {', '.join(missing_keys)}"
                )
            else:
                self.log_result(
                    "Credential store entries",
                    True,
                    "All expected keys present"
                )
                
        except Exception as e:
            self.log_result(
                "Credential store entries",
                False,
                f"Cleanup failed: {str(e)}"
            )