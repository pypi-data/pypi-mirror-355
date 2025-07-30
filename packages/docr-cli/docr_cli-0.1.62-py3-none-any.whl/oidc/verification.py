"""
Verification Operations
- Verify OIDC registrations are working correctly
- Check client registration, secrets, and API access
"""
import re
from typing import Dict, Optional
from utils import AWSUtils, ConsoleUtils, OIDCConfigManager, DynamoDBUtils, APIGatewayUtils
from utils.shared_console import get_shared_console


class VerificationStep:
    """Handle verification of OIDC registrations."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def verify_oidc_pattern_consistency_simple(self, stage: str) -> bool:
        """Simplified version for doctor commands that uses fixed directory structure."""
        from rich.text import Text
        from rich.panel import Panel
        
        # Create a cleaner header for the pattern check
        header_text = Text()
        header_text.append("🔍 ", style="")
        header_text.append("OIDC Pattern Consistency Check", style="bold cyan")
        
        header_panel = Panel(
            header_text,
            style="cyan",
            padding=(0, 1)
        )
        
        self.console.print(header_panel)
        
        try:
            # Use simplified config loading for doctor commands
            from doctor.base import BaseDoctorCheck
            
            # Check that config files exist for key apps
            apps_to_check = ["legislative-review", "oidc-manager"]
            all_configs_exist = True
            
            for app_name in apps_to_check:
                try:
                    config_path = BaseDoctorCheck.get_simple_config_path(app_name, stage)
                    if not config_path.exists():
                        self.console.print(f"     ❌ Config file not found for {app_name}: {config_path}")
                        all_configs_exist = False
                    else:
                        self.console.print(f"     ✅ Config file found for {app_name}")
                except Exception as e:
                    self.console.print(f"     ❌ Error checking config for {app_name}: {e}")
                    all_configs_exist = False
            
            return all_configs_exist
            
        except Exception as e:
            self.console.print(f"     ❌ Pattern consistency check failed: {e}")
            return False
    
    def _should_client_be_registered_with_api(self, app_name: str, api_name: str) -> bool:
        """Determine if a client should be registered with a specific API.
        
        Based on the reference pattern:
        - legislative-review client: registered with Legislative Review API + all component APIs
        - oidc-manager client: registered ONLY with OIDC Manager API
        - Components don't have their own clients
        """
        # Normalize names
        app_base = app_name.lower()
        api_base = api_name.lower().replace('-api', '').replace('_api', '')
        
        # Legislative Review client should be in:
        # - Legislative Review API
        # - All component APIs (cost, jobs, workspaces)
        if app_base == 'legislative-review':
            return api_base in ['legislative-review', 'legislativereview', 'legislative', 
                              'cost', 'costs', 'job', 'jobs', 'workspace', 'workspaces']
        
        # OIDC Manager client should ONLY be in OIDC Manager API
        if app_base == 'oidc-manager':
            return api_base in ['oidc', 'oidc-manager', 'oidcmanager']
        
        # Components don't have their own clients
        return False
    
    def verify_single_registration_simple(self, app: str, stage: str, show_header: bool = True, discovered_apis: Dict[str, str] = None, app_context: Optional[str] = None) -> bool:
        """Simplified version for doctor commands that uses fixed directory structure."""
        from doctor.base import BaseDoctorCheck
        
        try:
            # Check if config file exists using simplified path
            config_path = BaseDoctorCheck.get_simple_config_path(app, stage)
            if not config_path.exists():
                self.console.print(f"     ❌ Config file not found: {config_path}")
                return False
            
            self.console.print(f"     ✅ Config file exists: {config_path.name}")
            
            # Get developer initials from config
            from utils import AppConfig
            config = AppConfig.load_config()
            dev_initials = config.get('project', {}).get('developer_initials')
            
            # Check results storage
            results = {
                'client_in_dynamo': False,
                'client_id': None,
                'checks_passed': 0,
                'checks_total': 0
            }
            
            # Get DynamoDB client and table for all checks
            dynamodb = None
            table_name = None
            
            # 1. Check DynamoDB for client registration
            self.console.print("  1. Checking DynamoDB client registration...")
            results['checks_total'] += 1
            try:
                dynamodb, table_name = DynamoDBUtils.get_oidc_client_and_table(dev_initials)
                
                # Get client IDs for this specific app
                app_client_ids = DynamoDBUtils.get_client_ids_for_apps(dynamodb, table_name, [app], dev_initials)
                
                if app_client_ids:
                    results['client_in_dynamo'] = True
                    results['client_id'] = app_client_ids[0]
                    results['checks_passed'] += 1
                    self.console.print(f"     ✅ Client found in DynamoDB: {app_client_ids[0]}")
                else:
                    self.console.print(f"     ❌ No client found in DynamoDB for {app}-{dev_initials}")
                    
            except Exception as e:
                self.console.print(f"     ❌ DynamoDB check failed: {e}")
            
            # 2. Check credential store for secret
            self.console.print("  2. Checking credential store for secret...")
            results['checks_total'] += 1
            try:
                from utils.umd_credential_store import get_credential
                
                # Set up environment for credential store
                OIDCConfigManager.setup_oidc_credential_store_env(dev_initials, stage)
                
                # Get secret key from config (not client ID)
                from utils import AppConfig
                config = AppConfig.load_config()
                
                # Check if it's an application or component
                if app in config.get('applications', {}):
                    secret_key = config['applications'][app].get('secret_key')
                elif app in config.get('components', {}):
                    secret_key = config['components'][app].get('secret_key')
                else:
                    secret_key = None
                
                if not secret_key:
                    self.console.print(f"     ❌ No secret_key defined in config for {app}")
                else:
                    # Try to get the credential using the correct key
                    try:
                        credential = get_credential(secret_key)
                        if credential:
                            results['checks_passed'] += 1
                            self.console.print(f"     ✅ Secret found in credential store")
                        else:
                            self.console.print(f"     ❌ No secret found in credential store for key: {secret_key}")
                    except Exception:
                        # Credential not found
                        self.console.print(f"     ❌ No secret found in credential store for key: {secret_key}")
                    
            except Exception as e:
                self.console.print(f"     ❌ Credential store check failed: {e}")
            
            # 3. Check API registrations
            if results['client_id'] and discovered_apis:
                self.console.print("  3. Checking API registrations...")
                try:
                    for api_name, api_id in discovered_apis.items():
                        try:
                            # Check if this client SHOULD be registered with this API
                            should_be_registered = self._should_client_be_registered_with_api(app, api_name)
                            
                            if should_be_registered:
                                results['checks_total'] += 1
                                # Check if it actually IS registered
                                client_registered = DynamoDBUtils.check_client_registered_with_api(
                                    dynamodb, table_name, api_id, results['client_id']
                                )
                                
                                if client_registered:
                                    results['checks_passed'] += 1
                                    self.console.print(f"     ✅ Registered with {api_name} API")
                                else:
                                    self.console.print(f"     ❌ Not registered with {api_name} API")
                            else:
                                # Should NOT be registered with this API
                                client_registered = DynamoDBUtils.check_client_registered_with_api(
                                    dynamodb, table_name, api_id, results['client_id']
                                )
                                if client_registered:
                                    self.console.print(f"     ❌ Incorrectly registered with {api_name} API (should not be)")
                                    
                        except Exception as e:
                            self.console.print(f"     ❌ {api_name} API check failed: {e}")
                            
                except Exception as e:
                    self.console.print(f"     ❌ API registration check failed: {e}")
            
            # Calculate overall success
            # For doctor command, we consider it successful if:
            # 1. Client exists in DynamoDB (required)
            # 2. API registrations are correct (required) 
            # 3. Credential store is optional (may not be set up yet during initial registration)
            
            # Count API registration success
            api_checks_passed = True
            if results['client_id'] and discovered_apis:
                # Check if any API registrations that SHOULD exist are missing
                for api_name, api_id in discovered_apis.items():
                    if self._should_client_be_registered_with_api(app, api_name):
                        # This API should have the client registered
                        try:
                            if not DynamoDBUtils.check_client_registered_with_api(
                                dynamodb, table_name, api_id, results['client_id']
                            ):
                                api_checks_passed = False
                                break
                        except:
                            api_checks_passed = False
                            break
            
            # Overall success requires DynamoDB client AND correct API registrations
            overall_success = results['client_in_dynamo'] and api_checks_passed
            
            # Log summary
            if overall_success:
                if results['checks_total'] > 0:
                    self.console.print(f"\n    ✅ Overall: {results['checks_passed']}/{results['checks_total']} checks passed")
            else:
                if results['checks_total'] > 0:
                    self.console.print(f"\n    ❌ Overall: {results['checks_passed']}/{results['checks_total']} checks passed")
            
            return overall_success
            
        except Exception as e:
            self.console.print(f"     ❌ Verification failed for {app}: {str(e)}")
            return False
    
    def verify_single_registration(self, app: str, stage: str, show_header: bool = True, discovered_apis: Dict[str, str] = None, app_context: Optional[str] = None):
        """Verify a single OIDC registration is working correctly."""
        if show_header:
            self.console.print(f"\n[bold yellow]🔍 Final Verification - {app}[/bold yellow]")
            self.console.print("─" * 50)
        
        try:
            # Get project configuration using consolidated utility
            config, dev_initials = OIDCConfigManager.get_oidc_config(stage, app_context=app_context)
            
            # Get project root for frontend paths
            from utils import AppConfig
            project_root = AppConfig.get_project_root()
            
            # Get frontend paths using centralized method
            frontend_paths = AppConfig.get_all_frontend_paths()
            
            # Check results storage
            results = {
                'client_in_dynamo': False,
                'client_id': None,
                'secret_in_credstore': False,
                'frontend_config_root': False,
                'config_match': False,
                'api_registrations': {}
            }
            
            # 1. Check DynamoDB for client registration using consolidated utilities
            self.console.print("  1. Checking DynamoDB client registration...")
            try:
                dynamodb, table_name = DynamoDBUtils.get_oidc_client_and_table(dev_initials)
                
                # Get client IDs for this specific app
                app_client_ids = DynamoDBUtils.get_client_ids_for_apps(dynamodb, table_name, [app], dev_initials)
                
                if app_client_ids:
                    results['client_in_dynamo'] = True
                    results['client_id'] = app_client_ids[0]
                    self.console.print(f"     ✅ Client found: {app_client_ids[0]}")
                else:
                    self.console.print(f"     ❌ No client found for {app}-{dev_initials}")
                    
            except Exception as e:
                self.console.print(f"     ❌ DynamoDB check failed: {e}")
            
            # 2. Check credential store for secret using consolidated utility
            self.console.print("  2. Checking credential store for secret...")
            try:
                from utils.umd_credential_store import get_credential
                
                # Set up environment for credential store using consolidated utility
                OIDCConfigManager.setup_oidc_credential_store_env(dev_initials, stage)
                
                # Get the secret key from configuration if available
                from utils import AppConfig
                config = AppConfig.load_config()
                secret_key = None
                
                # Check if app is in applications or components
                if 'applications' in config and app in config['applications']:
                    secret_key = config['applications'][app].get('secret_key')
                elif 'components' in config and app in config['components']:
                    secret_key = config['components'][app].get('secret_key')
                
                # Check if secret_key not found in config
                if not secret_key:
                    self.console.print(f"     ❌ No secret_key defined in config for {app}")
                else:
                    # Try to get the credential using the correct key
                    try:
                        secret_value = get_credential(secret_key)
                        
                        if secret_value and len(secret_value) > 10:  # Basic check for non-empty secret
                            results['secret_in_credstore'] = True
                            self.console.print(f"     ✅ Secret stored correctly ({len(secret_value)} chars)")
                        else:
                            self.console.print(f"     ❌ No secret found in credential store for key: {secret_key}")
                    except Exception:
                        # Credential not found
                        self.console.print(f"     ❌ No secret found in credential store for key: {secret_key}")
                    
            except Exception as e:
                self.console.print(f"     ❌ Credential store check failed: {e}")
            
            # 3. Check frontend configuration files (only for application apps, not components)
            from utils import AppConfig
            if AppConfig.is_application(app) and app in frontend_paths:
                frontend_dir = frontend_paths[app]
                
                # Check root config file (primary location for generated configs)
                self.console.print("  3. Checking frontend config...")
                root_config = frontend_dir / ".env.production"
                if root_config.exists():
                    try:
                        with open(root_config, 'r') as f:
                            content = f.read()
                        
                        client_id_match = re.search(r'VITE_OIDC_CLIENT_ID="([^"]*)"', content)
                        if client_id_match:
                            frontend_client_id = client_id_match.group(1)
                            results['frontend_config_root'] = True
                            self.console.print(f"     ✅ Frontend config found: {frontend_client_id}")
                            
                            # Check if it matches DynamoDB client ID
                            if results['client_id'] and frontend_client_id == results['client_id']:
                                results['config_match'] = True
                                self.console.print(f"     ✅ Matches DynamoDB client ID")
                            else:
                                self.console.print(f"     ❌ Does not match DynamoDB client ID ({results['client_id']})")
                        else:
                            self.console.print(f"     ❌ No VITE_OIDC_CLIENT_ID found in frontend config")
                    except Exception as e:
                        self.console.print(f"     ❌ Frontend config read failed: {e}")
                else:
                    self.console.print(f"     ❌ Frontend config not found: {root_config}")
            
            # Check API registrations for this client
            if results['client_id']:
                # Adjust step numbering based on app type
                from utils import AppConfig
                step_num = "5" if AppConfig.is_application(app) else "3"
                self.console.print(f"  {step_num}. Checking API registrations...")
                try:
                    # Use discovered APIs or discover them dynamically
                    if not discovered_apis:
                        discovered_apis = APIGatewayUtils.get_all_api_gateway_ids(stage)
                    
                    all_apis = discovered_apis
                    
                    for api_name, api_id in all_apis.items():
                        try:
                            # Check if this client SHOULD be registered with this API
                            should_be_registered = self._should_client_be_registered_with_api(app, api_name)
                            
                            # Check if it actually IS registered
                            client_registered = DynamoDBUtils.check_client_registered_with_api(
                                dynamodb, table_name, api_id, results['client_id']
                            )
                            
                            # Only consider it a success if it matches what we expect
                            if should_be_registered:
                                results['api_registrations'][api_name] = client_registered
                                if client_registered:
                                    self.console.print(f"     ✅ Registered with {api_name} API")
                                else:
                                    self.console.print(f"     ❌ Not registered with {api_name} API")
                            else:
                                # Should NOT be registered with this API
                                if client_registered:
                                    self.console.print(f"     ❌ Incorrectly registered with {api_name} API (should not be)")
                                    results['api_registrations'][api_name] = False  # This is an error
                                else:
                                    # Not registered and shouldn't be - this is correct, don't count it
                                    pass
                                
                        except Exception as e:
                            self.console.print(f"     ❌ {api_name} API check failed: {e}")
                            results['api_registrations'][api_name] = False
                            
                except Exception as e:
                    self.console.print(f"     ❌ API registration check failed: {e}")
            
            # Summary for this app
            self.console.print(f"\n[bold]Summary for {app}:[/bold]")
            total_checks = 0
            passed_checks = 0
            
            # Client in DynamoDB
            total_checks += 1
            if results['client_in_dynamo']:
                passed_checks += 1
                self.console.print(f"  ✅ DynamoDB client registration")
            else:
                self.console.print(f"  ❌ DynamoDB client registration")
            
            # Secret in credential store
            total_checks += 1
            if results['secret_in_credstore']:
                passed_checks += 1
                self.console.print(f"  ✅ Credential store secret")
            else:
                self.console.print(f"  ❌ Credential store secret")
            
            # Frontend config (only for application apps, not components)
            from utils import AppConfig
            if AppConfig.is_application(app):
                # Check frontend config file
                total_checks += 1
                if results['frontend_config_root']:
                    passed_checks += 1
                    self.console.print(f"  ✅ Frontend config")
                else:
                    self.console.print(f"  ❌ Frontend config")
                
                # Check if config matches DynamoDB
                total_checks += 1
                if results['config_match']:
                    passed_checks += 1
                    self.console.print(f"  ✅ Config matches DynamoDB client ID")
                else:
                    self.console.print(f"  ❌ Config matches DynamoDB client ID")
            else:
                # Component apps (cost, jobs, workspaces) don't have frontend config files
                self.console.print(f"  ℹ️  Frontend config: N/A (component app)")
                # Note: we don't add to total_checks since this is not applicable
            
            # API registrations - only count APIs that should have this client
            api_count = len(results['api_registrations'])
            api_passed = sum(1 for registered in results['api_registrations'].values() if registered)
            
            # For total checks, we count the expected APIs, not all APIs
            expected_api_count = api_count  # This is already filtered by _should_client_be_registered_with_api
            total_checks += expected_api_count
            passed_checks += api_passed
            
            if api_passed == expected_api_count and expected_api_count > 0:
                self.console.print(f"  ✅ API registrations ({api_passed}/{expected_api_count})")
            else:
                self.console.print(f"  ❌ API registrations ({api_passed}/{expected_api_count})")
            
            # Overall status
            if passed_checks == total_checks:
                self.console.print(f"\n[bold green]🎉 {app} verification: ALL CHECKS PASSED ({passed_checks}/{total_checks})[/bold green]")
                return True
            else:
                if app in ["cost", "jobs", "workspaces"]:
                    # For component apps, explain that missing frontend config is expected
                    self.console.print(f"\n[bold yellow]✅ {app} verification: {passed_checks}/{total_checks} checks passed[/bold yellow]")
                    self.console.print(f"[dim]    Note: Component apps don't need frontend config files[/dim]")
                    return True  # Components are successful even without frontend config
                else:
                    self.console.print(f"\n[bold red]⚠️  {app} verification: {passed_checks}/{total_checks} checks passed[/bold red]")
                    return False
                
        except Exception as e:
            self.console.print(f"\n[red]❌ Verification failed for {app}: {e}[/red]")
            return False