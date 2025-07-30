"""
Application Configuration Management using TOML
Reads all configuration from ~/docr.toml

This class serves as a facade over focused configuration classes:
- ProjectConfig: handles project root, active app, developer initials
- StackConfig: handles stack names, API URLs, Lambda functions
- ComponentRegistry: handles component/application discovery and metadata  
- PathConfig: handles all file system paths and path utilities
"""
import tomllib
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from rich.console import Console

console = Console()


class AppConfig:
    """
    Application configuration facade.
    
    This class maintains backwards compatibility while internally delegating
    to focused configuration classes for better separation of concerns.
    """
    
    CONFIG_FILE = Path.home() / "docr.toml"
    
    @classmethod
    def _get_project_config(cls) -> 'ProjectConfig':
        """Get ProjectConfig instance with loaded configuration."""
        from .project_config import ProjectConfig
        config_data = cls.load_config()
        return ProjectConfig(config_data)
    
    @classmethod  
    def _get_stack_config(cls) -> 'StackConfig':
        """Get StackConfig instance with loaded configuration."""
        from .stack_config import StackConfig
        config_data = cls.load_config()
        return StackConfig(config_data)
    
    @classmethod
    def _get_component_registry(cls) -> 'ComponentRegistry':
        """Get ComponentRegistry instance with loaded configuration."""
        from .component_registry import ComponentRegistry
        config_data = cls.load_config()
        return ComponentRegistry(config_data)
    
    @classmethod
    def _get_path_config(cls) -> 'PathConfig':
        """Get PathConfig instance with loaded configuration."""
        from .path_config import PathConfig
        config_data = cls.load_config()
        project_root = Path(config_data['project']['root'])
        return PathConfig(config_data, project_root)
    
    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """
        Load configuration from TOML file.
        
        Raises:
            FileNotFoundError: If config file doesn't exist
            tomllib.TOMLDecodeError: If config file is corrupted
        """
        if not cls.CONFIG_FILE.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {cls.CONFIG_FILE}\n"
                "Please run 'docr setup' first to configure your project."
            )
        
        try:
            with open(cls.CONFIG_FILE, 'rb') as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise tomllib.TOMLDecodeError(
                f"Configuration file is corrupted: {cls.CONFIG_FILE}\n"
                f"Error: {e}\n"
                "Please delete the file and run 'docr setup' to regenerate it."
            )
    
    @classmethod
    def get_project_root(cls) -> Path:
        """Get project root directory from configuration."""
        return cls._get_project_config().get_project_root()
    
    
    @classmethod
    def discover_applications(cls) -> List[str]:
        """Get list of configured applications."""
        return cls._get_component_registry().discover_applications()
    
    @classmethod
    def discover_components(cls) -> List[str]:
        """Get list of configured components."""
        return cls._get_component_registry().discover_components()
    
    @classmethod
    def get_app_directory_name(cls, app_name: str) -> str:
        """Get the physical directory name for an application."""
        return cls._get_component_registry().get_app_directory_name(app_name)
    
    @classmethod
    def get_app_from_directory_name(cls, dir_name: str) -> str:
        """Get the logical application name from a directory name."""
        return cls._get_component_registry().get_app_from_directory_name(dir_name)
    
    @classmethod
    def get_app_backend_path(cls, app_name: str) -> str:
        """Get the backend path for an application."""
        return cls._get_path_config().get_app_backend_path(app_name)
    
    @classmethod
    def get_app_frontend_path(cls, app_name: str) -> str:
        """Get the frontend path for an application."""
        return cls._get_path_config().get_app_frontend_path(app_name)
    
    @classmethod
    def get_component_backend_path(cls, component_name: str) -> str:
        """Get the backend path for a component."""
        return cls._get_path_config().get_component_backend_path(component_name)
    
    @classmethod
    def get_component_frontend_path(cls, component_name: str) -> str:
        """Get the frontend path for a component."""
        return cls._get_path_config().get_component_frontend_path(component_name)
    
    # === ABSOLUTE PATH METHODS ===
    
    @classmethod
    def get_app_backend_dir(cls, app_name: str = None) -> Path:
        """Get absolute path to application backend directory."""
        return cls._get_path_config().get_app_backend_dir(app_name)
    
    @classmethod
    def get_app_frontend_dir(cls, app_name: str = None) -> Path:
        """Get absolute path to application frontend directory."""
        return cls._get_path_config().get_app_frontend_dir(app_name)
    
    @classmethod
    def get_component_backend_dir(cls, component_name: str) -> Path:
        """Get absolute path to component backend directory."""
        return cls._get_path_config().get_component_backend_dir(component_name)
    
    @classmethod
    def get_component_frontend_dir(cls, component_name: str) -> Path:
        """Get absolute path to component frontend directory."""
        return cls._get_path_config().get_component_frontend_dir(component_name)
    
    @classmethod
    def get_config_dir(cls, app_name: str = None) -> Path:
        """Get absolute path to application config directory."""
        return cls._get_path_config().get_config_dir(app_name)
    
    @classmethod
    def get_app_dir(cls, app_name: str = None) -> Path:
        """Get absolute path to application app directory."""
        return cls._get_path_config().get_app_dir(app_name)
    
    @classmethod
    def get_scripts_dir(cls, app_name: str = None) -> Path:
        """Get absolute path to application scripts directory."""
        return cls._get_path_config().get_scripts_dir(app_name)
    
    @classmethod
    def get_all_frontend_paths(cls) -> Dict[str, Path]:
        """Get all frontend paths for applications and components."""
        return cls._get_path_config().get_all_frontend_paths()
    
    @classmethod
    def get_component_metadata(cls, component: str) -> Dict[str, Any]:
        """Get metadata for a specific component."""
        return cls._get_component_registry().get_component_metadata(component)
    
    @classmethod
    def get_component_npm_package(cls, component: str) -> str:
        """Get npm package name for component."""
        return cls._get_component_registry().get_component_npm_package(component)
    
    @classmethod
    def get_component_npm_alias(cls, component: str) -> str:
        """Get npm alias for component."""
        return cls._get_component_registry().get_component_npm_alias(component)
    
    @classmethod
    def get_component_api_url(cls, component: str) -> str:
        """Get the API URL for component."""
        return cls._get_stack_config().get_component_api_url(component)
    
    @classmethod
    def get_component_lambda_function_name(cls, component: str) -> str:
        """Get Lambda function name for component."""
        return cls._get_stack_config().get_component_lambda_function_name(component)
    
    @classmethod
    def get_component_stack_name(cls, component: str, dev_initials: str = None) -> str:
        """Get CloudFormation stack name for component."""
        return cls._get_stack_config().get_component_stack_name(component, dev_initials)
    
    @classmethod
    def get_component_api_name(cls, component: str, dev_initials: str = None) -> str:
        """Get API Gateway name for component."""
        return cls._get_stack_config().get_component_api_name(component, dev_initials)
    
    @classmethod
    def get_component_client_name(cls, component: str) -> str:
        """Get client name for verify_clients."""
        return cls._get_component_registry().get_component_client_name(component)
    
    @classmethod
    def get_component_oidc_client_name(cls, component: str) -> str:
        """Get OIDC client name for component."""
        return cls._get_component_registry().get_component_oidc_client_name(component)
    
    @classmethod
    def get_application_oidc_client_name(cls, app: str) -> str:
        """Get OIDC client name for application."""
        return cls._get_component_registry().get_application_oidc_client_name(app)
    
    @classmethod
    def get_oidc_client_name(cls, app_or_component: str) -> str:
        """Get OIDC client name for any app or component."""
        return cls._get_component_registry().get_oidc_client_name(app_or_component)
    
    @classmethod
    def get_bootstrap_enabled_components(cls) -> List[str]:
        """Get list of components that support bootstrap."""
        return cls._get_component_registry().get_bootstrap_enabled_components()
    
    @classmethod
    def get_all_component_paths(cls) -> Dict[str, str]:
        """Get all component frontend paths as relative strings."""
        return cls._get_component_registry().get_all_component_paths()
    
    @classmethod
    def get_all_component_npm_packages(cls) -> Dict[str, str]:
        """Get all component npm package names."""
        return cls._get_component_registry().get_all_component_npm_packages()
    
    @classmethod
    def get_bootstrap_file_path(cls, endpoint: str, stage: str) -> Path:
        """Get path to bootstrap file for specific endpoint and stage."""
        return cls._get_path_config().get_bootstrap_file_path(endpoint, stage)
    
    @classmethod
    def get_expected_modules(cls) -> List[str]:
        """Get list of expected module directories for validation."""
        return cls._get_component_registry().get_expected_modules()
    
    @classmethod
    def setup_python_path(cls) -> None:
        """Add app directory to Python path for imports."""
        cls._get_path_config().setup_python_path()
    
    @classmethod
    def detect_current_component(cls) -> Optional[str]:
        """Detect which frontend component or application directory we're currently in."""
        return cls._get_path_config().detect_current_component()
    
    @classmethod
    def detect_current_backend(cls) -> Optional[Tuple[str, Path]]:
        """Detect which backend component directory we're currently in."""
        return cls._get_path_config().detect_current_backend()
    
    @classmethod
    def is_application(cls, name: str) -> bool:
        """Check if name is an application."""
        return cls._get_component_registry().is_application(name)
    
    @classmethod
    def is_component(cls, name: str) -> bool:
        """Check if name is a component."""
        return cls._get_component_registry().is_component(name)
    
    @classmethod
    def get_app_info(cls) -> Dict[str, Any]:
        """Get application configuration information for display."""
        return cls._get_project_config().get_app_info()
    
    # === PATH UTILITY METHODS ===
    
    @classmethod
    def ensure_directory(cls, path: Path) -> None:
        """Create directory if it doesn't exist."""
        cls._get_path_config().ensure_directory(path)
    
    @classmethod
    def get_relative_path(cls, path: Path, base: Path = None) -> str:
        """Get relative path from base directory."""
        return cls._get_path_config().get_relative_path(path, base)
    
    @classmethod
    def safe_resolve_path(cls, path: Path) -> Path:
        """Safely resolve path, expanding user directory and making absolute."""
        return cls._get_path_config().safe_resolve_path(path)
    
    @classmethod
    def validate_path_exists(cls, path: Path, path_type: str = "path") -> None:
        """Validate that a path exists, raise descriptive error if not."""
        cls._get_path_config().validate_path_exists(path, path_type)
    
    @classmethod
    def validate_directory_exists(cls, path: Path, dir_type: str = "directory") -> None:
        """Validate that a directory exists and is a directory."""
        cls._get_path_config().validate_directory_exists(path, dir_type)
    
    @classmethod
    def validate_file_exists(cls, path: Path, file_type: str = "file") -> None:
        """Validate that a file exists and is a file."""
        cls._get_path_config().validate_file_exists(path, file_type)
    
    @classmethod
    def join_paths(cls, *parts: str) -> Path:
        """Join path parts safely using pathlib instead of string concatenation."""
        return cls._get_path_config().join_paths(*parts)
    
    @classmethod
    def find_files_by_pattern(cls, directory: Path, pattern: str, recursive: bool = False) -> List[Path]:
        """Find files matching a pattern in a directory."""
        return cls._get_path_config().find_files_by_pattern(directory, pattern, recursive)
    
    @classmethod
    def get_parent_containing_file(cls, start_path: Path, filename: str, max_levels: int = 10) -> Optional[Path]:
        """Find the parent directory containing a specific file."""
        return cls._get_path_config().get_parent_containing_file(start_path, filename, max_levels)
    
    @classmethod
    def find_config_file(cls, stage: str, app_name: str = None) -> Optional[Path]:
        """Find first available config file for the given stage."""
        return cls._get_path_config().find_config_file(stage, app_name)
    
    # === OIDC DIRECTORY METHODS ===
    
    @classmethod
    def get_oidc_directory(cls, oidc_component: str) -> Optional[str]:
        """Get OIDC directory name for a component."""
        return cls._get_component_registry().get_oidc_directory(oidc_component)
    
    @classmethod
    def get_oidc_directory_path(cls, oidc_component: str) -> Optional[Path]:
        """Get absolute path to OIDC component directory."""
        return cls._get_path_config().get_oidc_directory_path(oidc_component)
    
    # === NEW METHODS FOR CLI REFACTOR ===
    
    @classmethod
    def get_developer_initials(cls) -> str:
        """Get developer initials from project config."""
        # Check for environment override first
        import os
        override = os.environ.get('DOCR_OVERRIDE_INITIALS')
        if override:
            return override.lower()
        
        # Fall back to stored config
        return cls._get_project_config().get_developer_initials()
    
    @classmethod
    def set_developer_initials_override(cls, developer_initials: str) -> None:
        """Validate and set developer initials override in environment."""
        import os
        if developer_initials:
            dev_initials = developer_initials.lower().strip()
            if len(dev_initials) != 3:
                raise ValueError("Developer initials must be exactly 3 characters")
            if not dev_initials.isalnum():
                raise ValueError("Developer initials must contain only letters and numbers")
            os.environ['DOCR_OVERRIDE_INITIALS'] = dev_initials
    
    @classmethod
    def clear_developer_initials_override(cls) -> None:
        """Clear developer initials override from environment."""
        import os
        os.environ.pop('DOCR_OVERRIDE_INITIALS', None)
    
    @classmethod
    def get_credstore_config(cls, app_name: str = None) -> dict:
        """Get credstore configuration."""
        if app_name is None:
            # Default to legislative-review for credstore operations
            app_name = "legislative-review"
        return cls._get_stack_config().get_credstore_config(app_name)
    
    @classmethod
    def get_sns_topic_arn(cls, app_or_component: str = None) -> Optional[str]:
        """Get SNS topic ARN for an application or component."""
        return cls._get_stack_config().get_sns_topic_arn(app_or_component)
    
    @classmethod
    def get_lambda_function_name(cls, app_or_component: str = None) -> Optional[str]:
        """Get Lambda function name for an application or component."""
        return cls._get_stack_config().get_lambda_function_name(app_or_component)
    
    @classmethod
    def get_stack_name(cls, app_or_component: str = None) -> Optional[str]:
        """Get stack name for an application or component."""
        return cls._get_stack_config().get_stack_name(app_or_component)
    
    @classmethod
    def get_api_url(cls, app_or_component: str = None, stage: str = "sandbox") -> Optional[str]:
        """Get API URL for an application or component for a specific stage."""
        return cls._get_stack_config().get_api_url(app_or_component, stage)
    
    @classmethod
    def get_component_lambda_env_var(cls, component: str) -> str:
        """Get the environment variable name for a component's Lambda function."""
        # Map component names to their Lambda environment variable names
        env_var_mapping = {
            "cost": "COST_LAMBDA_FUNCTION_NAME",
            "jobs": "JOB_LAMBDA_FUNCTION_NAME", 
            "workspaces": "WORKSPACES_LAMBDA_FUNCTION_NAME"
        }
        
        # Add application mappings
        applications = cls.discover_applications()
        for app in applications:
            if app == "legislative-review":
                env_var_mapping[app] = "LEGISLATIVE_REVIEW_LAMBDA_FUNCTION_NAME"
            elif app == "oidc-manager":
                env_var_mapping[app] = "OIDC_MANAGER_LAMBDA_FUNCTION_NAME"
        
        return env_var_mapping.get(component, f"{component.upper()}_LAMBDA_FUNCTION_NAME")