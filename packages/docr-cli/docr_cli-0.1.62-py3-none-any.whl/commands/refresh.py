"""Refresh configuration from AWS CloudFormation."""
import boto3
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from rich import print as rprint
import tomli_w
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

from utils import AppConfig, ConsoleUtils, AWSUtils


def refresh_config():
    """Refresh configuration with latest values from AWS CloudFormation."""
    console_utils = ConsoleUtils()
    
    rprint("\n[bold]Refreshing configuration from AWS...[/bold]")
    
    # Verify AWS credentials
    is_valid, message = AWSUtils.verify_aws_token()
    if is_valid:
        console_utils.print_success(message)
    else:
        console_utils.print_error(message, exit_code=1)
    
    # Load current config
    config = AppConfig.load_config()
    dev_initials = AppConfig.get_developer_initials()
    
    # Collect all stack names to query
    stack_names = []
    
    # Collect backend stack names
    for app_name, app_config in config.get('applications', {}).items():
        if stack_name := app_config.get('stack_name'):
            stack_names.append(stack_name)
        # Also add frontend stacks
        # Special case for oidc-manager which uses different naming
        if app_name == "oidc-manager":
            frontend_stack = f"{app_name}-{dev_initials}"
        else:
            frontend_stack = f"{app_name}-frontend-{dev_initials}"
        stack_names.append(frontend_stack)
    
    # Collect component stack names
    for comp_name, comp_config in config.get('components', {}).items():
        if stack_name := comp_config.get('stack_name'):
            stack_names.append(stack_name)
    
    # Add OIDC authorizer stack
    oidc_authorizer_stack = f"oidc-lambda-authorizer-shared-{dev_initials}"
    stack_names.append(oidc_authorizer_stack)
    
    # Fetch all stack outputs in parallel
    rprint("\n[cyan]Fetching stack outputs in parallel...[/cyan]")
    start_time = time.time()
    all_outputs = get_stack_outputs_batch(stack_names)
    fetch_time = time.time() - start_time
    rprint(f"[green]✓ Fetched outputs from {len(stack_names)} stacks in {fetch_time:.2f}s[/green]")
    
    # Track updates
    updates = []
    
    # Update applications
    rprint("\n[cyan]Updating application configurations...[/cyan]")
    for app_name, app_config in config.get('applications', {}).items():
        stack_name = app_config.get('stack_name')
        if stack_name and stack_name in all_outputs:
            rprint(f"  Checking {app_name} ({stack_name})...")
            
            stack_outputs = all_outputs[stack_name]
            
            # Get API URL - try both ApiUrl and FastApiFunctionUrl
            api_url = stack_outputs.get('ApiUrl') or stack_outputs.get('FastApiFunctionUrl')
            if api_url:
                old_url = app_config.get('stage_sandbox_api_url', '')
                app_config['stage_sandbox_api_url'] = api_url
                if old_url != api_url:
                    updates.append(f"{app_name} API URL: {api_url}")
                    rprint(f"    [green]✓ Updated API URL[/green]")
            
            # Get Lambda function name
            lambda_name = stack_outputs.get('FastSyncLambdaName')
            if lambda_name:
                old_name = app_config.get('lambda_function_name', '')
                app_config['lambda_function_name'] = lambda_name
                if old_name != lambda_name:
                    updates.append(f"{app_name} Lambda: {lambda_name}")
                    rprint(f"    [green]✓ Updated Lambda function name[/green]")
            
            # Get OIDC client table name (only for oidc-manager)
            if app_name == "oidc-manager":
                table_name = stack_outputs.get('OidcClientTableName')
                if table_name:
                    old_table = app_config.get('oidc_client_table_name', '')
                    app_config['oidc_client_table_name'] = table_name
                    if old_table != table_name:
                        updates.append(f"{app_name} OIDC Client Table: {table_name}")
                        rprint(f"    [green]✓ Updated OIDC Client Table Name[/green]")
            
            # Get SNS topic ARN for jobs (applications that support job submission)
            sns_arn = stack_outputs.get('JobTopicArn')
            if sns_arn:
                old_arn = app_config.get('sns_topic_arn', '')
                app_config['sns_topic_arn'] = sns_arn
                if old_arn != sns_arn:
                    updates.append(f"{app_name} SNS Topic: {sns_arn}")
                    rprint(f"    [green]✓ Updated SNS Topic ARN[/green]")
            
            # Get frontend URL for applications with frontends
            # Special case for oidc-manager which uses different naming
            if app_name == "oidc-manager":
                frontend_stack = f"{app_name}-{dev_initials}"
            else:
                frontend_stack = f"{app_name}-frontend-{dev_initials}"
            if frontend_stack in all_outputs:
                frontend_outputs = all_outputs[frontend_stack]
                
                frontend_url = frontend_outputs.get('CustomDomainName')
                if frontend_url:
                    if not frontend_url.startswith('https://'):
                        frontend_url = f"https://{frontend_url}"
                    old_frontend = app_config.get('stage_sandbox_frontend_url', '')
                    app_config['stage_sandbox_frontend_url'] = frontend_url
                    if old_frontend != frontend_url:
                        updates.append(f"{app_name} Frontend URL: {frontend_url}")
                        rprint(f"    [green]✓ Updated Frontend URL[/green]")
                
                # Get frontend bucket name
                bucket_name = frontend_outputs.get('FrontendBucketName')
                if bucket_name:
                    old_bucket = app_config.get('frontend_bucket_name', '')
                    app_config['frontend_bucket_name'] = bucket_name
                    if old_bucket != bucket_name:
                        updates.append(f"{app_name} Frontend Bucket: {bucket_name}")
                        rprint(f"    [green]✓ Updated Frontend Bucket Name[/green]")
                
                # Get CloudFront distribution ID
                distribution_id = frontend_outputs.get('CloudFrontDistributionId')
                if distribution_id:
                    old_dist = app_config.get('cloudfront_distribution_id', '')
                    app_config['cloudfront_distribution_id'] = distribution_id
                    if old_dist != distribution_id:
                        updates.append(f"{app_name} CloudFront Distribution: {distribution_id}")
                        rprint(f"    [green]✓ Updated CloudFront Distribution ID[/green]")
    
    # Update components
    rprint("\n[cyan]Updating component configurations...[/cyan]")
    for comp_name, comp_config in config.get('components', {}).items():
        stack_name = comp_config.get('stack_name')
        if stack_name and stack_name in all_outputs:
            rprint(f"  Checking {comp_name} ({stack_name})...")
            
            stack_outputs = all_outputs[stack_name]
            
            # Get API URL - try both ApiUrl and FastApiFunctionUrl
            api_url = stack_outputs.get('ApiUrl') or stack_outputs.get('FastApiFunctionUrl')
            if api_url:
                old_url = comp_config.get('stage_sandbox_api_url', '')
                comp_config['stage_sandbox_api_url'] = api_url
                if old_url != api_url:
                    updates.append(f"{comp_name} API URL: {api_url}")
                    rprint(f"    [green]✓ Updated API URL[/green]")
            
            # Get Lambda function name
            lambda_name = stack_outputs.get('FastSyncLambdaName')
            if lambda_name:
                old_name = comp_config.get('lambda_function_name', '')
                comp_config['lambda_function_name'] = lambda_name
                if old_name != lambda_name:
                    updates.append(f"{comp_name} Lambda: {lambda_name}")
                    rprint(f"    [green]✓ Updated Lambda function name[/green]")
            
            # Get SNS topic ARN if available (e.g., for jobs component)
            sns_arn = stack_outputs.get('SnsTopicArn')
            if sns_arn:
                old_arn = comp_config.get('sns_topic_arn', '')
                comp_config['sns_topic_arn'] = sns_arn
                if old_arn != sns_arn:
                    updates.append(f"{comp_name} SNS Topic: {sns_arn}")
                    rprint(f"    [green]✓ Updated SNS Topic ARN[/green]")
    
    # Update OIDC Authorizer configuration
    if oidc_authorizer_stack in all_outputs:
        rprint(f"\n[cyan]Updating OIDC Authorizer configuration...[/cyan]")
        rprint(f"  Checking oidc-authorizer ({oidc_authorizer_stack})...")
        
        stack_outputs = all_outputs[oidc_authorizer_stack]
        
        # Initialize OIDC section if not present
        if 'oidc' not in config:
            config['oidc'] = {}
        if 'authorizer' not in config['oidc']:
            config['oidc']['authorizer'] = {}
        
        # Store stack name
        config['oidc']['authorizer']['stack_name'] = oidc_authorizer_stack
        
        # Get authorizer Lambda ARN (actual output name)
        authorizer_arn = stack_outputs.get('OidcLambdaAuthorizerFunction')
        if authorizer_arn:
            old_arn = config['oidc']['authorizer'].get('authorizer_arn', '')
            config['oidc']['authorizer']['authorizer_arn'] = authorizer_arn
            if old_arn != authorizer_arn:
                updates.append(f"OIDC Authorizer ARN: {authorizer_arn}")
                rprint(f"    [green]✓ Updated Authorizer ARN[/green]")
        
        # Get authorizer function name
        function_name = stack_outputs.get('OidcLambdaAuthorizerFunctionName')
        if function_name:
            old_name = config['oidc']['authorizer'].get('function_name', '')
            config['oidc']['authorizer']['function_name'] = function_name
            if old_name != function_name:
                updates.append(f"OIDC Authorizer Function: {function_name}")
                rprint(f"    [green]✓ Updated Function Name[/green]")
        
        # Mark as deployed if we have the ARN
        if authorizer_arn:
            config['oidc']['authorizer']['deployed'] = True
    
    # Update timestamp
    import datetime
    config['project']['last_updated'] = datetime.datetime.now().isoformat()
    
    # Save updated config
    config_file = AppConfig.CONFIG_FILE
    with open(config_file, 'wb') as f:
        tomli_w.dump(config, f)
    
    # Summary
    if updates:
        rprint(f"\n[green]✓ Configuration refreshed with {len(updates)} updates:[/green]")
        for update in updates:
            rprint(f"  • {update}")
    else:
        rprint("\n[yellow]No updates found - configuration is already up to date[/yellow]")
    
    rprint(f"\n[dim]Configuration saved to: {config_file}[/dim]")


def get_stack_outputs_batch(stack_names: List[str]) -> Dict[str, Dict[str, str]]:
    """Get all outputs for multiple stacks in parallel using boto3.
    
    Returns a dict mapping stack_name -> {output_key: output_value}
    """
    cfn = boto3.client('cloudformation')
    results = {}
    
    def get_stack_outputs(stack_name: str) -> Tuple[str, Dict[str, str]]:
        """Get outputs for a single stack."""
        try:
            response = cfn.describe_stacks(StackName=stack_name)
            outputs = {}
            if response['Stacks'] and response['Stacks'][0].get('Outputs'):
                for output in response['Stacks'][0]['Outputs']:
                    outputs[output['OutputKey']] = output['OutputValue']
            return stack_name, outputs
        except Exception:
            return stack_name, {}
    
    # Fetch all stack outputs in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(get_stack_outputs, stack_name): stack_name 
                  for stack_name in stack_names}
        
        for future in as_completed(futures):
            stack_name, outputs = future.result()
            results[stack_name] = outputs
    
    return results


def get_stack_output(stack_name: str, output_key: str) -> Optional[str]:
    """Get a specific output value from a CloudFormation stack.
    
    Legacy function for backwards compatibility.
    """
    outputs = get_stack_outputs_batch([stack_name])
    return outputs.get(stack_name, {}).get(output_key)