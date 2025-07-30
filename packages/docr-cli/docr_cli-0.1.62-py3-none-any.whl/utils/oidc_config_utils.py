#!/usr/bin/env python3
"""
OIDC Configuration Management Utilities
Consolidates common OIDC configuration patterns to eliminate duplication.
"""
import os
from pathlib import Path
from typing import Tuple, Optional

from .config_utils import ConfigUtils
from .app_config import AppConfig


class OIDCConfigManager:
    """Manages OIDC-specific configuration loading and environment setup."""
    
    @staticmethod
    def get_oidc_config(stage: str = "sandbox", app_context: Optional[str] = None) -> Tuple[ConfigUtils, str]:
        """
        Get OIDC configuration and developer initials for given stage.
        
        Args:
            stage: Environment stage (sandbox, dev, qa, prod)
            app_context: Optional application context to use instead of detecting from directory
            
        Returns:
            Tuple of (ConfigUtils instance, developer_initials)
            
        Raises:
            RuntimeError: If project root or config cannot be found
        """
        from .app_config import AppConfig
        
        # If app_context is provided, use it directly
        if app_context:
            current_app = app_context
        else:
            # Detect current app from directory
            current_app = AppConfig.detect_current_component()
            if not current_app:
                # Try to detect from backend directory
                detected_backend = AppConfig.detect_current_backend()
                if detected_backend:
                    current_app, _ = detected_backend
            
            if not current_app:
                raise RuntimeError("Could not detect application from current directory")
        
        config = ConfigUtils(stage, current_app)
        dev_initials = AppConfig.get_developer_initials()
        
        return config, dev_initials
    
    @staticmethod
    def get_oidc_backend_dir() -> Path:
        """
        Get current application backend directory.
        
        Returns:
            Path to current application backend directory
        """
        from .app_config import AppConfig
        
        # Detect current app from directory
        current_app = AppConfig.detect_current_component()
        if not current_app:
            # Try to detect from backend directory
            detected_backend = AppConfig.detect_current_backend()
            if detected_backend:
                current_app, _ = detected_backend
        
        if not current_app:
            raise RuntimeError("Could not detect application from current directory")
        
        return AppConfig.get_app_backend_dir(current_app)
    
    @staticmethod
    def setup_oidc_credential_store_env(dev_initials: str, stage: str = "sandbox") -> None:
        """
        Set up credential store environment variables for OIDC.
        
        Args:
            dev_initials: Developer initials (e.g., 'cdm')
            stage: Environment stage (sandbox, dev, qa, prod)
        """
        os.environ["UMD_AH_CREDSTORE_TABLENAME"] = "UmdMockCredStore"
        os.environ["UMD_AH_ENVIRONMENT"] = stage
        os.environ["UMD_AH_PRODUCTSUITE"] = "oidc"
        os.environ["UMD_AH_PRODUCT"] = f"oidcauthorizer-{dev_initials}"
    
    @staticmethod
    def get_oidc_table_name(dev_initials: str) -> str:
        """
        Get OIDC DynamoDB table name for given developer initials.
        
        Args:
            dev_initials: Developer initials (e.g., 'cdm')
            
        Returns:
            DynamoDB table name for OIDC resources
        """
        return f"oidc-app{dev_initials.lower()}OidcResources"
    
    @staticmethod
    def get_oidc_scripts_dir() -> Path:
        """
        Get OIDC scripts directory path.
        
        Returns:
            Path to oidc-oidcauthorizer-serverless/scripts directory
            
        Raises:
            RuntimeError: If scripts directory not found
        """
        project_root = AppConfig.get_project_root()
        scripts_dir = project_root / "oidc-oidcauthorizer-serverless" / "scripts"
        
        if not scripts_dir.exists():
            raise RuntimeError(f"OIDC scripts directory not found: {scripts_dir}")
        
        return scripts_dir