"""Delete AWS CloudFormation stacks."""
import boto3
from typing import List, Dict, Any, Optional
from rich import print as rprint
from rich.table import Table
from rich.prompt import Confirm
from rich.live import Live
import typer
import time
from datetime import datetime

from utils import AppConfig, ConsoleUtils, AWSUtils


def analyze_stack_dependencies(cf_client, stacks_to_delete):
    """Analyze dependencies between stacks based on exports and imports."""
    dependencies = {}
    stack_names = [s['name'] for s in stacks_to_delete]
    
    for stack in stacks_to_delete:
        stack_name = stack['name']
        dependencies[stack_name] = []
        
        try:
            # Get exports from this stack
            response = cf_client.describe_stacks(StackName=stack_name)
            outputs = response['Stacks'][0].get('Outputs', [])
            
            # Check for exported outputs
            for output in outputs:
                if output.get('ExportName'):
                    # This stack exports something - check who imports it
                    try:
                        imports = cf_client.list_imports(ExportName=output['ExportName'])
                        for importing_stack in imports.get('Imports', []):
                            # Extract stack name from full stack ID/name
                            importing_stack_name = importing_stack.split('/')[-1] if '/' in importing_stack else importing_stack
                            # Check if the importing stack is in our deletion list
                            if importing_stack_name in stack_names:
                                dependencies[stack_name].append(importing_stack_name)
                    except:
                        pass
        except Exception as e:
            # If we can't get dependencies, we'll just proceed with normal order
            pass
    
    return dependencies


def order_stacks_by_dependencies(stacks_to_delete, dependencies):
    """Order stacks so that dependent stacks are deleted before their dependencies."""
    ordered = []
    stack_dict = {s['name']: s for s in stacks_to_delete}
    processed = set()
    
    def add_stack_and_dependents(stack_name):
        if stack_name in processed:
            return
        
        # First add all stacks that depend on this one
        for other_stack, deps in dependencies.items():
            if stack_name in deps and other_stack not in processed:
                add_stack_and_dependents(other_stack)
        
        # Then add this stack
        if stack_name in stack_dict:
            ordered.append(stack_dict[stack_name])
            processed.add(stack_name)
    
    # Process all stacks
    for stack in stacks_to_delete:
        add_stack_and_dependents(stack['name'])
    
    return ordered


def delete_stacks(
    developer_initials: str = typer.Option(None, "--developer-initials", "-d", help="Developer initials for stacks to delete (REQUIRED for safety)"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts")
):
    """Delete all CloudFormation stacks for the specified developer initials."""
    console_utils = ConsoleUtils()
    
    if not developer_initials:
        console_utils.print_error(
            "Developer initials are required for stack deletion.\n"
            "Use: docr delete stacks --developer-initials <initials>\n"
            "This safety measure prevents accidental deletion of wrong stacks.",
            exit_code=1
        )
    
    # Verify AWS credentials
    is_valid, message = AWSUtils.verify_aws_token()
    if is_valid:
        console_utils.print_success(message)
    else:
        console_utils.print_error(message, exit_code=1)
    
    # Use the explicitly provided developer initials instead of config
    dev_initials = developer_initials.lower()
    
    rprint(f"\n[bold]Searching for stacks with developer initials '[cyan]{dev_initials}[/cyan]'...[/bold]")
    
    # Initialize AWS clients
    cf = boto3.client('cloudformation')
    s3 = boto3.client('s3')
    ecr = boto3.client('ecr')
    logs = boto3.client('logs')
    
    # Collect all stacks to delete
    stacks_to_delete = []
    frontend_buckets = {}  # Stack name -> bucket name mapping
    document_buckets = {}  # Stack name -> document bucket mapping
    companion_ecr_repos = {}  # Stack name -> ECR repo mapping for companion stacks
    
    # Known stack patterns with their types and component mappings
    stack_patterns = [
        # Applications
        (f"legislative-review-{dev_initials}", "backend", "legislative-review"),
        (f"legislative-review-frontend-{dev_initials}", "frontend", "legislative-review"),
        (f"oidc-app-{dev_initials}", "backend", "oidc-manager"),
        (f"oidc-manager-{dev_initials}", "frontend", "oidc-manager"),
        
        # Components
        (f"costs-app-{dev_initials}", "component", "costs"),
        (f"jobs-app-{dev_initials}", "component", "jobs"),
        (f"workspaces-app-{dev_initials}", "component", "workspaces"),
        
        # Infrastructure
        (f"oidc-authorizer-{dev_initials}", "infrastructure", "oidc-authorizer"),
        (f"oidc-lambda-authorizer-shared-{dev_initials}", "infrastructure", "oidc-authorizer"),
    ]
    
    # Check each known stack pattern
    for stack_name, stack_type, component in stack_patterns:
        try:
            response = cf.describe_stacks(StackName=stack_name)
            stacks_to_delete.append({
                'name': stack_name,
                'type': stack_type,
                'component': component
            })
            
            # Get S3 buckets and document buckets from outputs
            outputs = response['Stacks'][0].get('Outputs', [])
            for output in outputs:
                output_key = output.get('OutputKey', '')
                if output_key in ['WebsiteBucket', 'FrontendBucketName']:
                    frontend_buckets[stack_name] = output['OutputValue']
                elif 'DocumentBucket' in output_key or 'S3Bucket' in output_key:
                    document_buckets[stack_name] = output['OutputValue']
        except:
            # Stack doesn't exist, continue
            pass
    
    # Collect companion stacks for known components
    # These are SAM CLI managed ECR repo stacks that need to be cleaned up
    companion_stack_prefixes = [
        f"legislative-review-{dev_initials}",
        f"oidc-app-{dev_initials}",
        f"costs-app-{dev_initials}",
        f"jobs-app-{dev_initials}",
        f"workspaces-app-{dev_initials}",
        f"oidc-lambda-authorizer-shared-{dev_initials}"
    ]
    
    try:
        paginator = cf.get_paginator('list_stacks')
        for page in paginator.paginate(StackStatusFilter=['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']):
            for stack_summary in page.get('StackSummaries', []):
                stack_name = stack_summary['StackName']
                # Check if this is a companion stack for one of our known components
                for prefix in companion_stack_prefixes:
                    if stack_name.startswith(prefix) and 'CompanionStack' in stack_name:
                        # This is a companion stack for one of our components
                        if not any(s['name'] == stack_name for s in stacks_to_delete):
                            # Extract the component name from the prefix
                            component_name = prefix.replace(f"-{dev_initials}", "")
                            stacks_to_delete.append({
                                'name': stack_name,
                                'type': 'companion',
                                'component': f'{component_name} (SAM ECR)'
                            })
                            
                            # Check for ECR repositories in companion stack
                            try:
                                resources = cf.describe_stack_resources(StackName=stack_name)
                                for resource in resources['StackResources']:
                                    if resource['ResourceType'] == 'AWS::ECR::Repository':
                                        # Store ECR repo for this companion stack
                                        companion_ecr_repos[stack_name] = resource['PhysicalResourceId']
                            except:
                                pass
                        break
    except Exception as e:
        rprint(f"[yellow]Warning: Could not list companion stacks: {str(e)}[/yellow]")
    
    if not stacks_to_delete:
        console_utils.print_warning(f"No stacks found for developer initials '{dev_initials}'")
        return
    
    # Collect ECR repositories for doc-review project components only
    ecr_repos_to_delete = []
    # Define expected ECR repo patterns for doc-review project
    ecr_repo_patterns = [
        f"legislative-review-{dev_initials}",
        f"oidc-app-{dev_initials}",
        f"costs-app-{dev_initials}",
        f"jobs-app-{dev_initials}",
        f"workspaces-app-{dev_initials}",
        f"oidc-lambda-authorizer-shared-{dev_initials}"
    ]
    
    try:
        paginator = ecr.get_paginator('describe_repositories')
        for page in paginator.paginate():
            for repo in page.get('repositories', []):
                repo_name = repo['repositoryName']
                # Check if repo matches any of our known doc-review project patterns
                for pattern in ecr_repo_patterns:
                    if repo_name.startswith(pattern) or pattern in repo_name:
                        ecr_repos_to_delete.append(repo_name)
                        break
    except Exception as e:
        rprint(f"[yellow]Warning: Could not list ECR repositories: {str(e)}[/yellow]")
    
    # Collect Lambda log groups for doc-review project components only
    log_groups_to_delete = []
    # Define expected log group patterns for doc-review project Lambda functions
    log_group_patterns = [
        f"/aws/lambda/legislative-review-{dev_initials}",
        f"/aws/lambda/oidc-app-{dev_initials}",
        f"/aws/lambda/costs-app-{dev_initials}",
        f"/aws/lambda/jobs-app-{dev_initials}",
        f"/aws/lambda/workspaces-app-{dev_initials}",
        f"/aws/lambda/oidc-lambda-authorizer-shared-{dev_initials}",
        f"/aws/lambda/OidcLambdaAuthorizer-{dev_initials}"
    ]
    
    try:
        paginator = logs.get_paginator('describe_log_groups')
        for page in paginator.paginate():
            for log_group in page.get('logGroups', []):
                log_group_name = log_group['logGroupName']
                # Check if log group matches any of our known doc-review project patterns
                for pattern in log_group_patterns:
                    if log_group_name.startswith(pattern) or pattern in log_group_name:
                        log_groups_to_delete.append(log_group_name)
                        break
    except Exception as e:
        rprint(f"[yellow]Warning: Could not list log groups: {str(e)}[/yellow]")
    
    # Display what will be deleted
    companion_count = sum(1 for s in stacks_to_delete if s['type'] == 'companion')
    main_count = len(stacks_to_delete) - companion_count
    
    rprint(f"\n[bold]Found {len(stacks_to_delete)} stacks for developer initials '[cyan]{dev_initials}[/cyan]':[/bold]")
    if companion_count > 0:
        rprint(f"  • {main_count} main stacks")
        rprint(f"  • {companion_count} SAM companion stacks (ECR repositories)\n")
    
    table = Table(title="Stacks to Delete")
    table.add_column("Stack Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Component", style="white")
    table.add_column("Additional Resources", style="red")
    
    for stack in stacks_to_delete:
        additional = []
        if stack['name'] in frontend_buckets:
            additional.append(f"S3 Bucket: {frontend_buckets[stack['name']]}")
        if stack['name'] in document_buckets:
            additional.append(f"Document Bucket: {document_buckets[stack['name']]}")
        if stack['name'] in companion_ecr_repos:
            additional.append(f"ECR Repository: {companion_ecr_repos[stack['name']]}")
        
        table.add_row(
            stack['name'],
            stack['type'],
            stack['component'],
            "\n".join(additional) if additional else "-"
        )
    
    console_utils.console.print(table)
    
    # Display additional resources that will be cleaned up
    if ecr_repos_to_delete or log_groups_to_delete:
        rprint("\n[bold]Additional resources to be cleaned up:[/bold]")
        if ecr_repos_to_delete:
            rprint(f"  • [yellow]{len(ecr_repos_to_delete)} ECR repositories[/yellow]")
            for repo in ecr_repos_to_delete[:5]:  # Show first 5
                rprint(f"    - {repo}")
            if len(ecr_repos_to_delete) > 5:
                rprint(f"    ... and {len(ecr_repos_to_delete) - 5} more")
        
        if log_groups_to_delete:
            rprint(f"  • [yellow]{len(log_groups_to_delete)} Lambda log groups[/yellow]")
            for log_group in log_groups_to_delete[:5]:  # Show first 5
                rprint(f"    - {log_group}")
            if len(log_groups_to_delete) > 5:
                rprint(f"    ... and {len(log_groups_to_delete) - 5} more")
    
    # Confirm deletion
    rprint("\n[bold red]WARNING:[/bold red] This will permanently delete all the stacks listed above!")
    rprint("This includes all resources created by these stacks (Lambda functions, API Gateways, S3 buckets, etc.)")
    
    if not yes and not Confirm.ask("\nDo you really want to delete these stacks?", default=False):
        console_utils.print_info("Stack deletion cancelled")
        return
    
    # Analyze stack dependencies
    stack_dependencies = analyze_stack_dependencies(cf, stacks_to_delete)
    
    # Add known dependency patterns for OIDC authorizer
    # The authorizer stack exports values that are used by app stacks
    for stack in stacks_to_delete:
        if 'oidc-lambda-authorizer-shared' in stack['name']:
            # This authorizer is used by oidc-app and potentially others
            for other_stack in stacks_to_delete:
                if other_stack['name'] in ['oidc-app-' + dev_initials, 'legislative-review-' + dev_initials]:
                    if other_stack['name'] not in stack_dependencies[stack['name']]:
                        stack_dependencies[stack['name']].append(other_stack['name'])
    
    # Order stacks for deletion based on dependencies
    ordered_stacks = order_stacks_by_dependencies(stacks_to_delete, stack_dependencies)
    
    # Delete stacks
    rprint("\n[bold]Starting cleanup and stack deletion...[/bold]")
    
    # Show dependencies if any found
    has_dependencies = any(deps for deps in stack_dependencies.values())
    if has_dependencies:
        rprint("\n[yellow]Detected stack dependencies - will delete in dependency order:[/yellow]")
        for stack_name, deps in stack_dependencies.items():
            if deps:
                rprint(f"  • {stack_name} exports values used by: {', '.join(deps)}")
    
    # Clean up ECR repositories first
    if ecr_repos_to_delete:
        rprint("\n[bold]Cleaning up ECR repositories...[/bold]")
        for repo_name in ecr_repos_to_delete:
            try:
                rprint(f"  Deleting ECR repository [cyan]{repo_name}[/cyan]...")
                delete_ecr_repository(ecr, repo_name)
                console_utils.print_success(f"  ✓ Deleted ECR repository {repo_name}")
            except Exception as e:
                console_utils.print_error(f"  ✗ Failed to delete ECR repository {repo_name}: {str(e)}")
    
    # Clean up log groups
    if log_groups_to_delete:
        rprint("\n[bold]Cleaning up Lambda log groups...[/bold]")
        for log_group_name in log_groups_to_delete:
            try:
                rprint(f"  Deleting log group [cyan]{log_group_name}[/cyan]...")
                delete_log_group(logs, log_group_name)
                console_utils.print_success(f"  ✓ Deleted log group {log_group_name}")
            except Exception as e:
                console_utils.print_error(f"  ✗ Failed to delete log group {log_group_name}: {str(e)}")
    
    # Now delete the stacks
    rprint("\n[bold]Deleting CloudFormation stacks...[/bold]")
    
    # Track failed deletions for retry
    failed_stacks = []
    skipped_stacks = []
    
    for stack in ordered_stacks:
        stack_name = stack['name']
        
        try:
            # Check stack status first
            try:
                response = cf.describe_stacks(StackName=stack_name)
                current_status = response['Stacks'][0]['StackStatus']
                
                # Skip if already being deleted
                if current_status in ['DELETE_IN_PROGRESS', 'DELETE_COMPLETE']:
                    rprint(f"  [yellow]Skipping {stack_name} - already {current_status}[/yellow]")
                    continue
                elif current_status == 'DELETE_FAILED':
                    rprint(f"  [yellow]Stack {stack_name} is in DELETE_FAILED state - will retry[/yellow]")
            except Exception as e:
                if 'does not exist' in str(e):
                    rprint(f"  [yellow]Skipping {stack_name} - already deleted[/yellow]")
                    continue
            
            # Empty S3 buckets first if this is a frontend stack
            if stack_name in frontend_buckets:
                bucket_name = frontend_buckets[stack_name]
                rprint(f"  Emptying S3 bucket [cyan]{bucket_name}[/cyan]...")
                try:
                    empty_s3_bucket(s3, bucket_name)
                except Exception as e:
                    rprint(f"  [yellow]Warning: Could not empty bucket {bucket_name}: {str(e)}[/yellow]")
            
            # Empty document buckets if any
            if stack_name in document_buckets:
                bucket_name = document_buckets[stack_name]
                rprint(f"  Emptying document bucket [cyan]{bucket_name}[/cyan]...")
                try:
                    empty_s3_bucket(s3, bucket_name)
                except Exception as e:
                    rprint(f"  [yellow]Warning: Could not empty bucket {bucket_name}: {str(e)}[/yellow]")
            
            # Delete ECR repository if this is a companion stack
            if stack_name in companion_ecr_repos:
                repo_name = companion_ecr_repos[stack_name]
                rprint(f"  Deleting ECR repository [cyan]{repo_name}[/cyan] from companion stack...")
                try:
                    delete_ecr_repository(ecr, repo_name)
                except Exception as e:
                    # Log but continue - the stack deletion might handle this
                    rprint(f"  [yellow]Warning: Could not delete ECR repo {repo_name}: {str(e)}[/yellow]")
            
            # Delete the stack
            rprint(f"  Deleting stack [cyan]{stack_name}[/cyan]...")
            cf.delete_stack(StackName=stack_name)
            console_utils.print_success(f"  ✓ Initiated deletion of {stack_name}")
            
        except Exception as e:
            error_msg = str(e)
            if 'as it is in use by' in error_msg:
                # This is a dependency issue - track for retry
                failed_stacks.append(stack)
                console_utils.print_warning(f"  ⚠ {stack_name} has dependencies - will retry after dependent stacks are deleted")
            else:
                console_utils.print_error(f"  ✗ Failed to delete {stack_name}: {error_msg}")
                failed_stacks.append(stack)
    
    rprint("\n[bold]Stack deletion initiated![/bold]")
    
    # Always monitor deletion progress (no prompt)
    monitor_stack_deletion(cf, [stack['name'] for stack in ordered_stacks], failed_stacks)


def monitor_stack_deletion(cf_client, stack_names: List[str], failed_stacks: List[Dict] = None):
    """Monitor the deletion progress of CloudFormation stacks with improved retry logic."""
    console_utils = ConsoleUtils()
    start_times = {stack: datetime.now() for stack in stack_names}
    failed_stacks = failed_stacks or []
    
    # Track stack states and retry information
    stack_states = {}
    retry_counts = {}
    last_retry_times = {}
    completed_stacks = set()
    
    def get_stack_status(stack_name):
        """Get the current status of a stack."""
        try:
            response = cf_client.describe_stacks(StackName=stack_name)
            return response['Stacks'][0]['StackStatus']
        except Exception as e:
            if 'does not exist' in str(e) or 'StackNotFoundException' in str(e.__class__.__name__):
                return 'DELETE_COMPLETE'
            return f'ERROR: {str(e)}'
    
    def should_retry_stack(stack_name, status):
        """Determine if a stack should be retried."""
        # Check if we haven't retried recently (wait at least 10 seconds between retries)
        last_retry = last_retry_times.get(stack_name, datetime.min)
        if (datetime.now() - last_retry).total_seconds() > 10:
            # Retry if DELETE_FAILED
            if 'DELETE_FAILED' in status:
                return True
            # Retry if stack exists but hasn't been deleted yet
            if status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
                return True
        return False
    
    def retry_stack_deletion(stack_name):
        """Retry deletion of a failed stack."""
        retry_count = retry_counts.get(stack_name, 0)
        try:
            # First check if the stack has a DELETE_FAILED status and needs manual intervention
            status = get_stack_status(stack_name)
            if 'DELETE_FAILED' in status:
                # Get the failure reason
                try:
                    response = cf_client.describe_stack_events(StackName=stack_name)
                    for event in response['StackEvents']:
                        if event.get('ResourceStatus') == 'DELETE_FAILED' and event.get('ResourceStatusReason'):
                            reason = event['ResourceStatusReason']
                            if 'is in use by' in reason:
                                # This is a dependency issue - automatic retry should work
                                break
                            elif 'The bucket you tried to delete is not empty' in reason:
                                # Need to empty bucket first
                                rprint(f"[yellow]Stack {stack_name} has non-empty S3 bucket, attempting to clean up...[/yellow]")
                                # The bucket should have been emptied already, but retry
                                break
                except:
                    pass
            
            cf_client.delete_stack(StackName=stack_name)
            retry_counts[stack_name] = retry_count + 1
            last_retry_times[stack_name] = datetime.now()
            return True, f"Retry #{retry_count + 1} initiated"
        except Exception as e:
            error_msg = str(e)
            if 'is in use by' in error_msg:
                return False, "Still has dependencies"
            return False, error_msg
    
    def get_status_table():
        """Generate a table showing current status of all stacks."""
        table = Table(title="Stack Deletion Progress", show_header=True)
        table.add_column("Stack Name", style="cyan", width=40)
        table.add_column("Status", style="yellow", width=25)
        table.add_column("Duration", style="white", width=10)
        table.add_column("Retries", style="magenta", width=8)
        
        all_deleted = True
        stacks_to_retry = []
        
        for stack_name in stack_names:
            if stack_name in completed_stacks:
                continue
                
            status = get_stack_status(stack_name)
            stack_states[stack_name] = status
            
            # Color code the status
            if status == 'DELETE_IN_PROGRESS':
                status_display = f"[yellow]{status}[/yellow]"
                all_deleted = False
            elif status == 'DELETE_COMPLETE':
                status_display = f"[green]{status}[/green]"
                completed_stacks.add(stack_name)
            elif 'DELETE_FAILED' in status:
                status_display = f"[red]{status}[/red]"
                all_deleted = False
                if should_retry_stack(stack_name, status):
                    stacks_to_retry.append(stack_name)
            elif 'ERROR' in status:
                # Handle error cases
                if 'does not exist' in status:
                    status_display = "[green]DELETE_COMPLETE[/green]"
                    completed_stacks.add(stack_name)
                else:
                    status_display = f"[red]{status}[/red]"
                    all_deleted = False
            else:
                # Other states (UPDATE_COMPLETE, CREATE_COMPLETE, etc.)
                status_display = f"[blue]{status}[/blue]"
                all_deleted = False
                # These stacks need deletion - always retry them
                if should_retry_stack(stack_name, status) or status in ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'UPDATE_ROLLBACK_COMPLETE']:
                    stacks_to_retry.append(stack_name)
            
            # Calculate duration
            duration = datetime.now() - start_times.get(stack_name, datetime.now())
            duration_str = f"{int(duration.total_seconds())}s"
            
            # Retry count
            retry_count = retry_counts.get(stack_name, 0)
            retry_str = str(retry_count) if retry_count > 0 else "-"
            
            table.add_row(stack_name, status_display, duration_str, retry_str)
        
        # Check if all tracked stacks are completed
        if len(completed_stacks) == len(stack_names):
            all_deleted = True
        
        return table, all_deleted, stacks_to_retry
    
    rprint("\n[bold]Monitoring stack deletion progress (press Ctrl+C to stop monitoring)...[/bold]")
    rprint("[dim]Tip: The system will automatically retry failed deletions due to dependencies[/dim]\n")
    
    try:
        last_update = datetime.now()
        retry_cycle = 0
        
        with Live(get_status_table()[0], refresh_per_second=0.5) as live:
            while True:
                table, all_deleted, stacks_to_retry = get_status_table()
                live.update(table)
                
                if all_deleted:
                    time.sleep(1)  # Give a moment to see the final status
                    break
                
                # Retry failed stacks periodically
                current_time = datetime.now()
                if stacks_to_retry and (current_time - last_update).total_seconds() > 10:
                    retry_cycle += 1
                    
                    # Clear the line and show retry messages without stopping live
                    retry_msg = f"[yellow]Retry cycle {retry_cycle}: Attempting to delete {len(stacks_to_retry)} stack(s)...[/yellow]"
                    
                    for stack_name in stacks_to_retry:
                        success, message = retry_stack_deletion(stack_name)
                        if success:
                            retry_msg += f"\n  [green]✓ {stack_name}: {message}[/green]"
                        else:
                            retry_msg += f"\n  [red]✗ {stack_name}: {message}[/red]"
                    
                    # Update the live display with retry info appended to the table
                    table_with_retry = table
                    table.caption = retry_msg
                    live.update(table_with_retry)
                    
                    last_update = current_time
                    time.sleep(2)  # Give time to see the retry messages
                    
                    # Clear caption for next update
                    table.caption = None
                    
                time.sleep(2)  # Update every 2 seconds for more responsive monitoring
        
        console_utils.print_success("\n✓ All stacks have been deleted successfully!")
        
        # Show summary
        if retry_cycle > 0:
            rprint(f"\n[dim]Deletion completed after {retry_cycle} retry cycle(s)[/dim]")
        
    except KeyboardInterrupt:
        rprint("\n[yellow]Monitoring stopped. Stacks will continue deleting in the background.[/yellow]")
        
        # Show current state
        in_progress = [s for s, status in stack_states.items() if 'IN_PROGRESS' in status]
        failed = [s for s, status in stack_states.items() if 'FAILED' in status]
        
        if in_progress:
            rprint(f"\n[yellow]Stacks still deleting:[/yellow]")
            for stack in in_progress:
                rprint(f"  • {stack}")
        
        if failed:
            rprint(f"\n[red]Failed stacks (may need manual intervention):[/red]")
            for stack in failed:
                rprint(f"  • {stack}")
        
        rprint("\nTo check status later, run:")
        rprint("  [cyan]aws cloudformation list-stacks --stack-status-filter DELETE_IN_PROGRESS DELETE_FAILED[/cyan]")


def delete_ecr_repository(ecr_client, repo_name: str):
    """Delete an ECR repository and all its images."""
    try:
        ecr_client.delete_repository(repositoryName=repo_name, force=True)
    except Exception as e:
        if 'RepositoryNotFoundException' not in str(e):
            raise


def delete_log_group(logs_client, log_group_name: str):
    """Delete a CloudWatch log group."""
    try:
        logs_client.delete_log_group(logGroupName=log_group_name)
    except Exception as e:
        if 'ResourceNotFoundException' not in str(e):
            raise


def empty_s3_bucket(s3_client, bucket_name: str):
    """Empty all objects from an S3 bucket."""
    try:
        # List all objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name)
        
        delete_keys = []
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    delete_keys.append({'Key': obj['Key']})
                    
                    # Delete in batches of 1000 (AWS limit)
                    if len(delete_keys) >= 1000:
                        s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': delete_keys}
                        )
                        delete_keys = []
        
        # Delete any remaining objects
        if delete_keys:
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': delete_keys}
            )
            
        # Also delete all versions if versioning is enabled
        paginator = s3_client.get_paginator('list_object_versions')
        pages = paginator.paginate(Bucket=bucket_name)
        
        delete_keys = []
        for page in pages:
            # Delete object versions
            if 'Versions' in page:
                for version in page['Versions']:
                    delete_keys.append({
                        'Key': version['Key'],
                        'VersionId': version['VersionId']
                    })
            
            # Delete delete markers
            if 'DeleteMarkers' in page:
                for marker in page['DeleteMarkers']:
                    delete_keys.append({
                        'Key': marker['Key'],
                        'VersionId': marker['VersionId']
                    })
            
            # Delete in batches
            if len(delete_keys) >= 1000:
                s3_client.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': delete_keys}
                )
                delete_keys = []
        
        # Delete any remaining versions
        if delete_keys:
            s3_client.delete_objects(
                Bucket=bucket_name,
                Delete={'Objects': delete_keys}
            )
            
    except Exception as e:
        # If bucket doesn't exist or we don't have permissions, continue
        if 'NoSuchBucket' not in str(e):
            raise