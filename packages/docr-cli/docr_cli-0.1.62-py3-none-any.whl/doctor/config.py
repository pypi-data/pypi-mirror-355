"""Configuration verification implementation."""
from pathlib import Path
import re
from typing import Dict
from .base import BaseDoctorCheck
from utils import AppConfig, ConfigUtils
from utils.stack_config import StackConfig


class ConfigDoctor(BaseDoctorCheck):
    """Verify backend and frontend configuration files."""
    
    def check(self) -> bool:
        """Verify configuration files have correct values."""
        self.console_utils.print_step(1, 2, "Checking backend configurations")
        self._check_backend_configs()
        
        self.console_utils.print_step(2, 2, "Checking frontend configurations")
        self._check_frontend_configs()
        
        return self.results['failed'] == 0
    
    def _check_backend_configs(self):
        """Check backend config files (config/config.sandbox)."""
        config = AppConfig.load_config()
        dev_initials = AppConfig.get_developer_initials()
        
        # Check only applications and components that need config files
        for app_type in ['applications']:  # Only check applications for now
            if app_type not in config:
                continue
                
            for app_name, app_config in config[app_type].items():
                # Check if this backend needs a config file
                if 'backend_registry' in config and app_name in config['backend_registry']:
                    backend_config = config['backend_registry'][app_name]
                    config_format = backend_config.get('config_format', 'env')
                    
                    # Skip if no config needed
                    if config_format == 'none':
                        continue
                
                try:
                    backend_dir = AppConfig.get_app_backend_dir(app_name)
                    config_file = backend_dir / "config" / f"config.{self.stage}"
                    
                    if not config_file.exists():
                        self.log_result(
                            f"{app_name} backend config",
                            False,
                            f"Config file not found: {config_file}"
                        )
                        continue
                    
                    # Load and validate config
                    try:
                        config_utils = ConfigUtils(self.stage, app_name)
                        
                        # Check required values from docr config
                        expected_values = self._get_expected_backend_values(app_name)
                        
                        for key, expected_value in expected_values.items():
                            actual_value = config_utils.get_variable(key)
                            
                            if actual_value == expected_value:
                                self.log_result(
                                    f"{app_name} {key}",
                                    True,
                                    f"Correct value"
                                )
                            else:
                                # Special handling for OIDC table mismatch
                                if key == 'UMD_AH_OIDC_CLIENT_TABLE' and app_name == 'oidc-manager':
                                    error_msg = (
                                        f"OIDC table has wrong initials! "
                                        f"Expected: {expected_value}, Got: {actual_value}\n"
                                        f"        This causes IAM permission errors. Run 'docr refresh' then 'docr config backend oidc-manager --force'"
                                    )
                                else:
                                    error_msg = f"Expected: {expected_value}, Got: {actual_value}"
                                
                                if self.fix:
                                    # Fix the config file
                                    self._fix_backend_config(config_file, key, expected_value)
                                    self.log_result(
                                        f"{app_name} {key}",
                                        True,
                                        f"Fixed: {actual_value} -> {expected_value}",
                                        fix_attempted=True
                                    )
                                else:
                                    self.log_result(
                                        f"{app_name} {key}",
                                        False,
                                        error_msg
                                    )
                                    
                    except Exception as e:
                        self.log_result(
                            f"{app_name} backend config",
                            False,
                            f"Error loading config: {str(e)}"
                        )
                        
                except Exception as e:
                    self.log_result(
                        f"{app_name} backend directory",
                        False,
                        f"Error accessing backend: {str(e)}"
                    )
    
    def _check_frontend_configs(self):
        """Check frontend config files (.env.production)."""
        config = AppConfig.load_config()
        
        # Only check applications that have frontends
        if 'applications' not in config:
            return
            
        for app_name, app_config in config['applications'].items():
            try:
                # Get frontend directory for this application
                frontend_dir = AppConfig.get_app_frontend_dir(app_name)
                
                # Check root config (.env.production)
                root_config = frontend_dir / ".env.production"
                
                expected_values = self._get_expected_frontend_values(app_name)
                
                if root_config.exists():
                    self._check_frontend_config_file(
                        root_config, f"{app_name} frontend config", expected_values
                    )
                else:
                    self.log_result(
                        f"{app_name} frontend config",
                        False,
                        f"Config file not found: {root_config}"
                    )
                    
            except Exception as e:
                self.log_result(
                    f"{app_name} frontend config",
                    False,
                    f"Error accessing frontend: {str(e)}"
                )
    
    def _get_expected_backend_values(self, app_name: str) -> Dict[str, str]:
        """Get expected backend config values from docr config."""
        config = AppConfig.load_config()
        dev_initials = AppConfig.get_developer_initials()
        
        expected = {}
        
        # Check values based on the application
        if app_name == 'legislative-review':
            # Use the actual config values from the TOML as the expected values
            # since those are the authoritative source
            if 'applications' in config and app_name in config['applications']:
                app_config = config['applications'][app_name]
                
                # Check for environment variable mappings
                if 'backend_registry' in config and app_name in config['backend_registry']:
                    backend_config = config['backend_registry'][app_name]
                    env_var_mappings = backend_config.get('env_var_mappings', {})
                    
                    for env_var, toml_key in env_var_mappings.items():
                        if toml_key in app_config:
                            expected[env_var] = app_config[toml_key]
        
        elif app_name == 'oidc-manager':
            # For OIDC manager, check the OIDC client table name contains correct initials
            if 'applications' in config and app_name in config['applications']:
                app_config = config['applications'][app_name]
                
                # Check for environment variable mappings
                if 'backend_registry' in config and app_name in config['backend_registry']:
                    backend_config = config['backend_registry'][app_name]
                    env_var_mappings = backend_config.get('env_var_mappings', {})
                    
                    for env_var, toml_key in env_var_mappings.items():
                        if toml_key in app_config:
                            if env_var == 'UMD_AH_OIDC_CLIENT_TABLE':
                                # Verify table name contains correct initials
                                table_name = app_config[toml_key]
                                expected_pattern = f"oidc-app{dev_initials}OidcResources"
                                
                                # Check if table name matches expected pattern
                                if f"app{dev_initials}" not in table_name:
                                    # Table name has wrong initials
                                    expected[env_var] = expected_pattern
                                else:
                                    # Table name is correct
                                    expected[env_var] = table_name
                            else:
                                expected[env_var] = app_config[toml_key]
        
        return expected
    
    def _get_expected_frontend_values(self, app_name: str) -> Dict[str, str]:
        """Get expected frontend config values."""
        config = AppConfig.load_config()
        stack_config = StackConfig(config)
        expected = {}
        
        # Main API URL
        main_api_url = stack_config.get_api_url(app_name, self.stage)
        if main_api_url:
            expected['VITE_API_URL'] = main_api_url
        
        # Component API URLs (for applications that need them)
        if app_name == 'legislative-review':
            component_apis = {
                'costs': 'VITE_COSTS_API_URL',
                'jobs': 'VITE_JOBS_API_URL',
                'workspaces': 'VITE_WORKSPACES_API_URL'
            }
            
            for component, env_var_name in component_apis.items():
                api_url = stack_config.get_api_url(component, self.stage)
                if api_url:
                    expected[env_var_name] = api_url
        
        # OIDC Authority
        expected['VITE_OIDC_AUTHORITY'] = 'https://shib.idm.dev.umd.edu/'
        
        # OIDC Client ID - we'll skip this check since it changes during registration
        # and doctor oidc already checks this properly
        
        return expected
    
    def _check_frontend_config_file(self, config_file: Path, name: str, expected_values: Dict[str, str]):
        """Check a single frontend config file for expected values."""
        try:
            with open(config_file, 'r') as f:
                content = f.read()
            
            all_good = True
            for key, expected_value in expected_values.items():
                # Look for the key in the file (handle both quoted and unquoted values)
                pattern = rf'{key}=([^\n]*)'
                match = re.search(pattern, content)
                
                if match:
                    actual_value = match.group(1).strip().strip('"')
                    if actual_value == expected_value:
                        self.log_result(
                            f"{name} {key}",
                            True,
                            "Correct value"
                        )
                    else:
                        all_good = False
                        if self.fix:
                            content = re.sub(pattern, f'{key}={expected_value}', content)
                            with open(config_file, 'w') as f:
                                f.write(content)
                            self.log_result(
                                f"{name} {key}",
                                True,
                                f"Fixed value",
                                fix_attempted=True
                            )
                        else:
                            self.log_result(
                                f"{name} {key}",
                                False,
                                f"Expected: {expected_value}, Got: {actual_value}"
                            )
                else:
                    all_good = False
                    self.log_result(
                        f"{name} {key}",
                        False,
                        "Key not found in config file"
                    )
            
                
        except Exception as e:
            self.log_result(
                name,
                False,
                f"Error reading config: {str(e)}"
            )
    
    
    def _fix_backend_config(self, config_file: Path, key: str, value: str):
        """Fix a value in backend config file."""
        try:
            with open(config_file, 'r') as f:
                lines = f.readlines()
            
            # Look for the key and update it
            updated = False
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key}="):
                    lines[i] = f"{key}={value}\n"
                    updated = True
                    break
            
            # If key not found, append it
            if not updated:
                lines.append(f"\n{key}={value}\n")
            
            with open(config_file, 'w') as f:
                f.writelines(lines)
                
        except Exception as e:
            self.console_utils.print_error(f"Failed to fix config: {str(e)}")