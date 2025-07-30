#!/usr/bin/env python3
"""
DynamoDB Utilities for OIDC Operations
Consolidates DynamoDB patterns used across OIDC modules.
"""
import boto3
from typing import List, Dict, Tuple, Any


class DynamoDBUtils:
    """Utilities for OIDC DynamoDB operations."""
    
    @staticmethod
    def get_oidc_client_and_table(dev_initials: str) -> Tuple[boto3.client, str]:
        """
        Get DynamoDB client and OIDC table name.
        
        Args:
            dev_initials: Developer initials (e.g., 'cdm')
            
        Returns:
            Tuple of (DynamoDB client, table_name)
        """
        client = boto3.client('dynamodb', region_name='us-east-1')
        table_name = f"oidc-app{dev_initials.lower()}OidcResources"
        return client, table_name
    
    @staticmethod
    def scan_oidc_clients(client, table_name: str, app_filter: str = None) -> List[Dict[str, Any]]:
        """
        Scan for OIDC client configurations with optional app filtering.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            app_filter: Optional app name to filter by (e.g., 'legislative-review')
            
        Returns:
            List of client configuration items
        """
        try:
            response = client.scan(
                TableName=table_name,
                FilterExpression='PK = :pk AND attribute_exists(client_name)',
                ExpressionAttributeValues={
                    ':pk': {'S': 'ORG#UMD#CLIENT'}
                }
            )
            
            items = response.get('Items', [])
            
            if app_filter:
                # Filter items by app name in client_name
                filtered_items = []
                for item in items:
                    client_name = item.get('client_name', {}).get('S', '')
                    if client_name.startswith(f"{app_filter}-"):
                        filtered_items.append(item)
                return filtered_items
            
            return items
            
        except Exception as e:
            raise RuntimeError(f"Failed to scan OIDC clients: {e}")
    
    @staticmethod
    def get_client_ids_for_apps(client, table_name: str, apps: List[str], dev_initials: str) -> List[str]:
        """
        Get all client IDs for specific apps.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            apps: List of app names to find clients for
            dev_initials: Developer initials for filtering
            
        Returns:
            List of client IDs
        """
        client_ids = []
        
        for app in apps:
            items = DynamoDBUtils.scan_oidc_clients(client, table_name, app_filter=app)
            for item in items:
                client_name = item.get('client_name', {}).get('S', '')
                if client_name.startswith(f"{app}-{dev_initials}"):
                    client_id = item['SK']['S'].replace('CLIENT#', '')
                    client_ids.append(client_id)
        
        return client_ids
    
    @staticmethod
    def get_api_allowed_clients(client, table_name: str, api_id: str) -> List[str]:
        """
        Get allowed clients for specific API.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            api_id: API Gateway ID
            
        Returns:
            List of allowed client IDs
        """
        try:
            response = client.get_item(
                TableName=table_name,
                Key={
                    'PK': {'S': 'ORG#UMD#API'},
                    'SK': {'S': f'API#{api_id}'}
                }
            )
            
            if 'Item' in response:
                allowed_clients = response['Item'].get('allowedClients', {}).get('L', [])
                return [client.get('S', str(client)) for client in allowed_clients]
            
            return []
            
        except Exception as e:
            raise RuntimeError(f"Failed to get allowed clients for API {api_id}: {e}")
    
    @staticmethod
    def update_api_allowed_clients(client, table_name: str, api_id: str, client_ids: List[str]) -> None:
        """
        Update allowed clients for specific API.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            api_id: API Gateway ID
            client_ids: List of client IDs to set as allowed
        """
        try:
            # Convert client IDs to DynamoDB format
            allowed_clients = [{'S': client_id} for client_id in client_ids]
            
            client.update_item(
                TableName=table_name,
                Key={
                    'PK': {'S': 'ORG#UMD#API'},
                    'SK': {'S': f'API#{api_id}'}
                },
                UpdateExpression='SET allowedClients = :clients, updatedAt = :updated',
                ExpressionAttributeValues={
                    ':clients': {'L': allowed_clients},
                    ':updated': {'S': __import__('datetime').datetime.now().isoformat()}
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Failed to update allowed clients for API {api_id}: {e}")
    
    @staticmethod
    def remove_clients_from_api(client, table_name: str, api_id: str, client_ids_to_remove: List[str]) -> List[str]:
        """
        Remove specific clients from API's allowed list.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            api_id: API Gateway ID
            client_ids_to_remove: List of client IDs to remove
            
        Returns:
            List of removed client IDs (for logging)
        """
        try:
            # Get current allowed clients
            current_clients = DynamoDBUtils.get_api_allowed_clients(client, table_name, api_id)
            
            # Filter out clients to remove
            removed_clients = []
            new_clients = []
            
            for client_id in current_clients:
                if client_id in client_ids_to_remove:
                    removed_clients.append(client_id)
                else:
                    new_clients.append(client_id)
            
            # Update with filtered list
            if len(new_clients) != len(current_clients):
                DynamoDBUtils.update_api_allowed_clients(client, table_name, api_id, new_clients)
            
            return removed_clients
            
        except Exception as e:
            raise RuntimeError(f"Failed to remove clients from API {api_id}: {e}")
    
    @staticmethod
    def delete_client_configuration(client, table_name: str, client_id: str) -> None:
        """
        Delete client configuration from DynamoDB.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            client_id: Client ID to delete
        """
        try:
            client.delete_item(
                TableName=table_name,
                Key={
                    'PK': {'S': 'ORG#UMD#CLIENT'},
                    'SK': {'S': f'CLIENT#{client_id}'}
                }
            )
        except Exception as e:
            raise RuntimeError(f"Failed to delete client configuration {client_id}: {e}")
    
    @staticmethod
    def check_client_registered_with_api(client, table_name: str, api_id: str, client_id: str) -> bool:
        """
        Check if client is registered with specific API.
        
        Args:
            client: DynamoDB client
            table_name: OIDC resources table name
            api_id: API Gateway ID
            client_id: Client ID to check
            
        Returns:
            True if client is registered with API
        """
        try:
            allowed_clients = DynamoDBUtils.get_api_allowed_clients(client, table_name, api_id)
            return client_id in allowed_clients
        except Exception:
            return False