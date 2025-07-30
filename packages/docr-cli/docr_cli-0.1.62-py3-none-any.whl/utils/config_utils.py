#!/usr/bin/env python3
"""
Stage-specific configuration utilities.
Handles loading stage config files (config.sandbox, config.dev, etc.) 
and setting up environment variables for subprocesses.

For TOML configuration management, use AppConfig instead.
"""
import os
from pathlib import Path
from typing import Dict, Optional, List
from dotenv import dotenv_values


class ConfigUtils:
    """
    Stage-specific configuration management.
    
    This class loads environment-specific config files (config.sandbox, config.dev, etc.)
    and provides utilities for setting up environment variables for subprocesses.
    
    **When to use ConfigUtils vs AppConfig:**
    - Use ConfigUtils for: Loading stage-specific env files, setting up subprocess environments
    - Use AppConfig for: TOML configuration, stack names, API URLs, developer initials
    
    **Primary use cases:**
    - Setting up environment variables for subprocess calls
    - Loading legacy stage-specific configuration files
    - Setting up credential store environment variables
    """
    
    def __init__(self, stage: str = "sandbox", app_name: str = None):
        """Initialize with stage (sandbox, dev, qa, prod) and optional app name."""
        self.stage = stage
        self.app_name = app_name
        self.config_path = self._get_config_path()
        self.config = self._load_config()
        
    def _get_config_path(self) -> Path:
        """Get config file path for stage."""
        from .app_config import AppConfig
        
        # If app_name not provided, try to detect from current directory
        app_name = self.app_name
        if not app_name:
            # Try to detect current app
            detected = AppConfig.detect_current_component()
            if detected:
                app_name = detected
            else:
                # Try to detect from backend directory
                detected_backend = AppConfig.detect_current_backend()
                if detected_backend:
                    app_name, _ = detected_backend
        
        if not app_name:
            raise ValueError(
                "Could not detect application from current directory.\n"
                "Please run this command from within an application or component directory,\n"
                "or ensure your working directory is properly configured."
            )
        
        try:
            config_dir = AppConfig.get_config_dir(app_name)
        except (RuntimeError, ValueError):
            # Fallback to relative path if AppConfig not available
            config_dir = Path(__file__).parent.parent.parent / "config"
            
        config_path = config_dir / f"config.{self.stage}"
        return config_path
    
    def _load_config(self) -> Dict[str, str]:
        """Load and parse config file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}\n"
                f"Please ensure you have a config.{self.stage} file in the config directory."
            )
        
        # Use dotenv_values for consistent parsing
        return dict(dotenv_values(self.config_path))
    
    
    def get_variable(self, name: str, default: Optional[str] = None) -> Optional[str]:
        """Get any variable from config (not just CLI_ prefixed)."""
        return self.config.get(name, default)
    
    # Removed get_api_url method - use AppConfig.get_api_url() instead
    
    def setup_environment(self, include_credential_store: bool = True, 
                         env_filter: Optional[List[str]] = None) -> None:
        """
        Set specific environment variables from config.
        
        **IMPORTANT**: This method should only set the minimum required environment
        variables for the specific operation being performed. Do not set all config
        variables globally.
        
        Args:
            include_credential_store: Whether to set credential store variables
            env_filter: Specific list of environment variables to set. If None,
                       sets a minimal default set.
        
        Common usage patterns:
        - For verify_clients: Pass env_filter with API_URL and LAMBDA_FUNCTION_NAME vars
        - For jobs: SNS_TOPIC_ARN is set separately, credential store may be needed
        - For credstore operations: Only credential store vars are needed
        """
        if env_filter is None:
            # Default minimal set - only set variables that are commonly needed
            # across multiple operations. Most operations should pass explicit filters.
            env_filter = []
        
        # Only set specifically requested environment variables
        for key in env_filter:
            if key in self.config:
                os.environ[key] = self.config[key]
        
        # Set up credential store if requested
        if include_credential_store:
            self.setup_credential_store()
    
    def setup_credential_store(self) -> None:
        """
        Set up credential store environment variables.
        
        The UMD credential store requires these specific environment variables:
        - UMD_AH_CREDSTORE_TABLENAME: DynamoDB table name (always 'UmdMockCredStore')
        - UMD_AH_ENVIRONMENT: Environment/stage (e.g., 'sandbox', 'dev', 'qa', 'prod')
        - UMD_AH_PRODUCTSUITE: Product suite name (always 'aisolutions' for this project)
        - UMD_AH_PRODUCT: Stack name from TOML config (identifies the specific product)
        
        These variables are used by utils/umd_credential_store.py for:
        - Encrypting/decrypting credentials with proper encryption context
        - Storing credentials in the correct DynamoDB table partition
        - Ensuring credentials are isolated by environment and product
        """
        # Get stack name from TOML config
        from .app_config import AppConfig
        
        # Use the app_name we stored during init
        app_name = self.app_name
        if not app_name:
            # Try to detect current app
            detected = AppConfig.detect_current_component()
            if detected:
                app_name = detected
            else:
                # Try to detect from backend directory
                detected_backend = AppConfig.detect_current_backend()
                if detected_backend:
                    app_name, _ = detected_backend
        
        if not app_name:
            raise ValueError(
                "Could not detect application from current directory.\n"
                "Please run this command from within an application or component directory,\n"
                "or ensure your working directory is properly configured."
            )
        
        stack_name = AppConfig.get_stack_name(app_name)
        if not stack_name:
            raise ValueError(
                f"Missing required configuration: stack_name\n"
                f"Run 'docr refresh' to update configuration from CloudFormation outputs."
            )
        
        os.environ['UMD_AH_CREDSTORE_TABLENAME'] = 'UmdMockCredStore'
        os.environ['UMD_AH_ENVIRONMENT'] = self.stage
        os.environ['UMD_AH_PRODUCTSUITE'] = 'aisolutions'
        os.environ['UMD_AH_PRODUCT'] = stack_name
    
    def normalize_api_urls(self) -> None:
        """
        Normalize API URL environment variables for compatibility.
        
        Handles legacy naming differences (COST vs COSTS, JOB vs JOBS).
        Only used by verify_clients.py - consider moving this logic there.
        """
        # Handle COST_API_URL vs COSTS_API_URL
        if 'COSTS_API_URL' in os.environ and 'COST_API_URL' not in os.environ:
            os.environ['COST_API_URL'] = os.environ['COSTS_API_URL']
        elif 'COST_API_URL' in self.config and 'COSTS_API_URL' not in os.environ:
            os.environ['COSTS_API_URL'] = self.config['COST_API_URL']
        
        # Handle JOB_API_URL vs JOBS_API_URL
        if 'JOBS_API_URL' not in os.environ and 'JOB_API_URL' in os.environ:
            os.environ['JOBS_API_URL'] = os.environ['JOB_API_URL']
        elif 'JOB_API_URL' in self.config and 'JOBS_API_URL' not in os.environ:
            os.environ['JOBS_API_URL'] = self.config['JOB_API_URL']
    
    
    def validate_required_variables(self, required_vars: List[str]) -> None:
        """
        Validate that all required variables are present.
        
        Args:
            required_vars: List of required variable names
            
        Raises:
            ValueError: If any required variables are missing
        """
        missing = []
        for var in required_vars:
            if not self.get_variable(var):
                missing.append(var)
        
        if missing:
            raise ValueError(
                f"Missing required configuration variables: {', '.join(missing)}\n"
                f"Please add these to {self.config_path}"
            )
    
    @staticmethod
    def get_available_stages() -> List[str]:
        """Get list of available configuration stages."""
        config_dir = Path(__file__).parent.parent.parent / "config"
        stages = []
        
        for config_file in sorted(config_dir.glob("config.*")):
            if config_file.suffix not in ['.example', '.bak', '.old']:
                stage = config_file.name.split('.', 1)[1]
                stages.append(stage)
        
        return stages