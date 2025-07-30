#!/usr/bin/env python3
"""
Direct Lambda invoke client for CLI scripts.
Provides HTTP-like interface using Lambda direct invocation.
"""
import os
import json
import boto3
from typing import Dict, Any, Optional
from pathlib import Path
import subprocess
from functools import lru_cache
from loguru import logger

from .console_utils import ConsoleUtils
from .config_utils import ConfigUtils


class DirectInvokeClient:
    """Client for direct Lambda invocation with HTTP-like interface."""
    
    def __init__(self, component: str, stage: str = "sandbox"):
        """
        Initialize direct invoke client.
        
        Args:
            component: Component name (active application, workspaces, cost, jobs)
            stage: Environment stage
        """
        self.component = component
        self.stage = stage
        self.console_utils = ConsoleUtils()
        
        # Initialize AWS Lambda client
        self.lambda_client = boto3.client('lambda')
        self.region = boto3.Session().region_name or 'us-east-1'
        
        # Get Lambda function name
        self.function_name = self._get_lambda_function_name()
        
        logger.info(f"Initialized DirectInvokeClient for {component}")
        logger.info(f"Lambda Function: {self.function_name}")
        logger.info(f"AWS Region: {self.region}")
    
    @lru_cache(maxsize=4)
    def _get_lambda_function_name(self) -> str:
        """
        Get Lambda function name for the component.
        First checks environment variable, then gets from TOML config.
        """
        # Check for environment variable first
        from .app_config import AppConfig
        
        # Build env var mapping dynamically from component metadata
        env_var_mapping = {
            comp: AppConfig.get_component_lambda_env_var(comp)
            for comp in AppConfig.discover_components()
        }
        
        # Add application mappings
        applications = AppConfig.discover_applications()
        for app in applications:
            if app == "legislative-review":
                env_var_mapping[app] = "LEGISLATIVE_REVIEW_LAMBDA_FUNCTION_NAME"
            elif app == "oidc-manager":
                env_var_mapping[app] = "OIDC_MANAGER_LAMBDA_FUNCTION_NAME"
        
        env_var = env_var_mapping.get(self.component)
        if env_var and os.environ.get(env_var):
            return os.environ[env_var]
        
        # Get from TOML config
        lambda_name = AppConfig.get_lambda_function_name(self.component)
        if not lambda_name:
            self.console_utils.print_error(
                f"Lambda function name not found for {self.component}.\n"
                "Run 'docr refresh' to update configuration from AWS.",
                exit_code=1
            )
        
        return lambda_name
    
    def _discover_lambda_function_name(self) -> str:
        """Discover Lambda function name from CloudFormation stack."""
        # Get developer initials from TOML config
        from .app_config import AppConfig
        dev_initials = AppConfig.get_developer_initials()
        
        # Build stack name based on component
        from .app_config import AppConfig
        
        # Build stack name mapping dynamically from component metadata
        stack_name_mapping = {
            comp: AppConfig.get_component_stack_name(comp, dev_initials)
            for comp in AppConfig.discover_components()
        }
        
        # Add application mappings
        applications = AppConfig.discover_applications()
        for app in applications:
            stack_name_mapping[app] = f"{app}-{dev_initials}"
        
        stack_name = stack_name_mapping.get(self.component)
        if not stack_name:
            self.console_utils.print_error(
                f"Unknown component: {self.component}",
                exit_code=1
            )
        
        logger.info(f"Looking up Lambda function in stack: {stack_name}")
        
        # Query CloudFormation for the Lambda function
        try:
            cf_client = boto3.client('cloudformation')
            
            # Get stack outputs
            response = cf_client.describe_stacks(StackName=stack_name)
            stack = response['Stacks'][0]
            
            # Look for BackendFunction in outputs
            for output in stack.get('Outputs', []):
                if output['OutputKey'] == 'BackendFunctionName':
                    return output['OutputValue']
            
            # If not in outputs, query resources
            resources = cf_client.list_stack_resources(StackName=stack_name)
            
            for resource in resources['StackResourceSummaries']:
                # Look for Lambda function resource
                if (resource['ResourceType'] == 'AWS::Lambda::Function' and
                    'BackendFunction' in resource['LogicalResourceId']):
                    return resource['PhysicalResourceId']
            
            # If still not found, try a more specific pattern
            # The Lambda function usually follows pattern: {stack-name}-ApiStack-{id}-BackendFunction-{id}
            lambda_client = boto3.client('lambda')
            paginator = lambda_client.get_paginator('list_functions')
            
            for page in paginator.paginate():
                for function in page['Functions']:
                    fn_name = function['FunctionName']
                    if (stack_name in fn_name and 
                        'BackendFunction' in fn_name and
                        'ApiStack' in fn_name):
                        return fn_name
            
            self.console_utils.print_error(
                f"Could not find Lambda function for stack {stack_name}. "
                f"Please ensure the stack is deployed.",
                exit_code=1
            )
            
        except Exception as e:
            self.console_utils.print_error(
                f"Failed to discover Lambda function: {str(e)}\n"
                f"Please ensure AWS credentials are configured and stack {stack_name} exists.",
                exit_code=1
            )
    
    def invoke(self, 
               method: str,
               path: str,
               headers: Optional[Dict[str, str]] = None,
               json_data: Optional[Dict[str, Any]] = None,
               data: Optional[str] = None,
               params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Invoke Lambda with HTTP-like parameters.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API path
            headers: HTTP headers
            json_data: JSON body data (will be serialized)
            data: Raw body data (for non-JSON like YAML)
            params: Query string parameters
            
        Returns:
            Response dictionary with statusCode, headers, and body
        """
        # Build event to mimic API Gateway
        event = {
            "httpMethod": method,
            "path": path,
            "queryStringParameters": params or {},
            "headers": headers or {},
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "direct-invoke",
                "httpMethod": method,
                "path": path,
                "stage": "direct",
                "requestId": "direct-invoke-request",
                "authorizer": {
                    "lambda": {
                        "client_name": "docr-cli"
                    }
                }
            },
            "isBase64Encoded": False
        }
        
        # Extract path parameters from the path (e.g., /admin/bootstrap/{appkey})
        # This mimics what API Gateway does
        path_params = {}
        import re
        
        # Handle common patterns in our APIs
        # Pattern for /admin/bootstrap/{appkey} and /admin/bootstrap/{appkey}/data
        bootstrap_pattern = r'^/admin/bootstrap/([^/]+)(?:/data)?$'
        match = re.match(bootstrap_pattern, path)
        if match:
            path_params["appkey"] = match.group(1)
            event["pathParameters"] = path_params
            logger.debug(f"Extracted path parameters: {path_params}")
            
            # For bootstrap endpoints, add globaladmin entitlement for the specific app
            appkey = match.group(1)
            event["requestContext"]["authorizer"]["lambda"]["entitlements"] = [
                f"aisolutions:docreview:{appkey}:globaladmins"
            ]
        
        # Pattern for other endpoints with appkey
        generic_appkey_pattern = r'^/([^/]+)/([^/]+)/([^/]+)$'
        if not path_params and re.match(generic_appkey_pattern, path):
            # Add more patterns as needed
            pass
        
        # Add body
        if json_data is not None:
            event["body"] = json.dumps(json_data)
            if "headers" not in event:
                event["headers"] = {}
            event["headers"]["Content-Type"] = "application/json"
        elif data is not None:
            event["body"] = data
        
        logger.info(f"Invoking Lambda {self.function_name}")
        logger.info(f"Path: {path}")
        if path_params:
            logger.info(f"Path parameters: {path_params}")
        logger.debug(f"Full event: {json.dumps(event, indent=2)}")
        
        try:
            # Invoke Lambda
            response = self.lambda_client.invoke(
                FunctionName=self.function_name,
                InvocationType='RequestResponse',
                Payload=json.dumps(event)
            )
            
            # Parse response
            payload = json.loads(response['Payload'].read())
            
            # Check for Lambda execution errors
            if 'errorMessage' in payload:
                logger.error(f"Lambda execution error: {payload.get('errorMessage')}")
                return {
                    "statusCode": 500,
                    "body": json.dumps({"detail": payload.get('errorMessage')})
                }
            
            return payload
            
        except Exception as e:
            logger.error(f"Failed to invoke Lambda: {str(e)}")
            return {
                "statusCode": 500,
                "body": json.dumps({"detail": f"Lambda invocation failed: {str(e)}"})
            }
    
    def get(self, path: str, headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """HTTP GET request."""
        return self.invoke("GET", path, headers=headers, params=params)
    
    def post(self, path: str, headers: Optional[Dict[str, str]] = None,
             json_data: Optional[Dict[str, Any]] = None,
             data: Optional[str] = None) -> Dict[str, Any]:
        """HTTP POST request."""
        return self.invoke("POST", path, headers=headers, json_data=json_data, data=data)
    
    def put(self, path: str, headers: Optional[Dict[str, str]] = None,
            json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP PUT request."""
        return self.invoke("PUT", path, headers=headers, json_data=json_data)
    
    def delete(self, path: str, headers: Optional[Dict[str, str]] = None,
               json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """HTTP DELETE request."""
        return self.invoke("DELETE", path, headers=headers, json_data=json_data)