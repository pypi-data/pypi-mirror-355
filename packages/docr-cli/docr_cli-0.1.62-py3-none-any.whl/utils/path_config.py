"""
Path configuration management.
Handles all file system paths for applications, components, and utilities.
"""
from pathlib import Path
from typing import Dict, Any, Optional, Tuple


class PathConfig:
    """Manages all file system paths and path utilities."""
    
    def __init__(self, config_data: Dict[str, Any], project_root: Path):
        self.config_data = config_data
        self.project_root = project_root
    
    # === RELATIVE PATH METHODS ===
    
    def get_app_backend_path(self, app_name: str) -> str:
        """Get the backend path for an application."""
        app_config = self.config_data['applications'].get(app_name, {})
        return app_config.get('backend_path', '')
    
    def get_app_frontend_path(self, app_name: str) -> str:
        """Get the frontend path for an application."""
        app_config = self.config_data['applications'].get(app_name, {})
        return app_config.get('frontend_path', '')
    
    def get_component_backend_path(self, component_name: str) -> str:
        """Get the backend path for a component."""
        component_config = self.config_data['components'].get(component_name, {})
        return component_config.get('backend_path', '')
    
    def get_component_frontend_path(self, component_name: str) -> str:
        """Get the frontend path for a component."""
        component_config = self.config_data['components'].get(component_name, {})
        return component_config.get('frontend_path', '')
    
    # === ABSOLUTE PATH METHODS ===
    
    def get_app_backend_dir(self, app_name: str = None) -> Path:
        """Get absolute path to application backend directory."""
        if app_name is None:
            raise ValueError("app_name parameter is required")
        
        backend_path = self.get_app_backend_path(app_name)
        return self.project_root / backend_path
    
    def get_app_frontend_dir(self, app_name: str = None) -> Path:
        """Get absolute path to application frontend directory."""
        if app_name is None:
            raise ValueError("app_name parameter is required")
        
        frontend_path = self.get_app_frontend_path(app_name)
        return self.project_root / frontend_path
    
    def get_component_backend_dir(self, component_name: str) -> Path:
        """Get absolute path to component backend directory."""
        backend_path = self.get_component_backend_path(component_name)
        return self.project_root / backend_path
    
    def get_component_frontend_dir(self, component_name: str) -> Path:
        """Get absolute path to component frontend directory."""
        frontend_path = self.get_component_frontend_path(component_name)
        return self.project_root / frontend_path
    
    def get_config_dir(self, app_name: str = None) -> Path:
        """Get absolute path to application config directory."""
        if app_name is None:
            raise ValueError("app_name parameter is required")
        
        backend_dir = self.get_app_backend_dir(app_name)
        return backend_dir / "config"
    
    def get_app_dir(self, app_name: str = None) -> Path:
        """Get absolute path to application app directory."""
        if app_name is None:
            raise ValueError("app_name parameter is required")
        
        backend_dir = self.get_app_backend_dir(app_name)
        return backend_dir / "app"
    
    def get_scripts_dir(self, app_name: str = None) -> Path:
        """Get absolute path to application scripts directory."""
        if app_name is None:
            raise ValueError("app_name parameter is required")
        
        backend_dir = self.get_app_backend_dir(app_name)
        return backend_dir / "scripts"
    
    def get_all_frontend_paths(self) -> Dict[str, Path]:
        """Get all frontend paths for applications and components."""
        frontend_paths = {}
        
        # Add application frontend paths
        for app_name in self.config_data.get('applications', {}):
            frontend_path = self.get_app_frontend_path(app_name)
            frontend_paths[app_name] = self.project_root / frontend_path
        
        # Add component frontend paths  
        for component_name in self.config_data.get('components', {}):
            frontend_path = self.get_component_frontend_path(component_name)
            frontend_paths[component_name] = self.project_root / frontend_path
        
        return frontend_paths
    
    def get_bootstrap_file_path(self, endpoint: str, stage: str) -> Path:
        """Get path to bootstrap file for specific endpoint and stage."""
        backend_dir = self.get_app_backend_dir()
        return backend_dir / "config" / "bootstrap" / stage / f"{endpoint}.yml"
    
    def get_oidc_directory_path(self, oidc_component: str) -> Optional[Path]:
        """Get absolute path to OIDC component directory."""
        dir_name = self.config_data.get('oidc', {}).get('directories', {}).get(oidc_component)
        if not dir_name:
            return None
        
        return self.project_root / dir_name
    
    def find_config_file(self, stage: str, app_name: str = None) -> Optional[Path]:
        """Find first available config file for the given stage."""
        if app_name is None:
            raise ValueError("app_name parameter is required")
        
        config_dir = self.get_config_dir(app_name)
        
        # Look for config files in order of preference
        possible_files = [
            config_dir / f"config.{stage}",
            config_dir / f"config.{stage}.json",
            config_dir / f"config.{stage}.yaml",
            config_dir / f"config.{stage}.yml"
        ]
        
        for config_file in possible_files:
            if config_file.exists():
                return config_file
        
        return None
    
    # === DETECTION METHODS ===
    
    def detect_current_component(self) -> Optional[str]:
        """Detect which frontend component or application directory we're currently in."""
        cwd = Path.cwd()
        
        # Check if we're in a component frontend directory
        for component_name, component_config in self.config_data.get('components', {}).items():
            frontend_path = self.get_component_frontend_path(component_name)
            abs_frontend_path = self.project_root / frontend_path
            
            if cwd == abs_frontend_path or abs_frontend_path in cwd.parents:
                return component_name
        
        # Check if we're in an application frontend directory
        for app_name, app_config in self.config_data.get('applications', {}).items():
            frontend_path = self.get_app_frontend_path(app_name)
            abs_frontend_path = self.project_root / frontend_path
            
            if cwd == abs_frontend_path or abs_frontend_path in cwd.parents:
                return app_name
        
        return None
    
    def detect_current_backend(self) -> Optional[Tuple[str, Path]]:
        """Detect which backend component directory we're currently in."""
        cwd = Path.cwd()
        
        # Check current directory and all parents
        for current_path in [cwd] + list(cwd.parents):
            # Check if we're in an application backend directory
            for app_name, app_config in self.config_data.get('applications', {}).items():
                backend_path = self.get_app_backend_path(app_name)
                abs_backend_path = self.project_root / backend_path
                
                if current_path == abs_backend_path:
                    if (current_path / "samconfig.toml").exists() or (current_path / "template.yaml").exists():
                        return app_name, current_path
            
            # Check for component backends
            for component_name, component_config in self.config_data.get('components', {}).items():
                backend_path = self.get_component_backend_path(component_name)
                abs_backend_path = self.project_root / backend_path
                
                if current_path == abs_backend_path:
                    if (current_path / "samconfig.toml").exists() or (current_path / "template.yaml").exists():
                        return component_name, current_path
            
            # Check for OIDC directories
            oidc_config = self.config_data.get('oidc', {})
            for oidc_name, oidc_info in oidc_config.items():
                if oidc_name == 'directories':
                    continue  # Skip the directories mapping
                
                if isinstance(oidc_info, dict) and 'directory_name' in oidc_info:
                    directory_name = oidc_info['directory_name']
                    abs_oidc_path = self.project_root / directory_name
                    
                    if current_path == abs_oidc_path:
                        if (current_path / "samconfig.toml").exists() or (current_path / "template.yaml").exists():
                            return f'oidc-{oidc_name}', current_path
        
        return None
    
    # === UTILITY METHODS ===
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """Create directory if it doesn't exist."""
        path.mkdir(parents=True, exist_ok=True)
    
    def get_relative_path(self, path: Path, base: Path = None) -> str:
        """Get relative path from base directory."""
        if base is None:
            base = self.project_root
        
        try:
            return str(path.relative_to(base))
        except ValueError:
            return str(path)
    
    @staticmethod
    def safe_resolve_path(path: Path) -> Path:
        """Safely resolve path, expanding user directory and making absolute."""
        return path.expanduser().resolve()
    
    @staticmethod
    def validate_path_exists(path: Path, path_type: str = "path") -> None:
        """
        Validate that a path exists, raise descriptive error if not.
        
        Args:
            path: Path to validate
            path_type: Description of what this path is (e.g., "config file", "backend directory")
            
        Raises:
            FileNotFoundError: If path doesn't exist
        """
        if not path.exists():
            raise FileNotFoundError(f"{path_type.capitalize()} not found: {path}")
    
    @staticmethod
    def validate_directory_exists(path: Path, dir_type: str = "directory") -> None:
        """
        Validate that a directory exists and is a directory.
        
        Args:
            path: Path to validate
            dir_type: Description of what this directory is
            
        Raises:
            FileNotFoundError: If path doesn't exist
            NotADirectoryError: If path exists but is not a directory
        """
        if not path.exists():
            raise FileNotFoundError(f"{dir_type.capitalize()} not found: {path}")
        if not path.is_dir():
            raise NotADirectoryError(f"Path exists but is not a directory: {path}")
    
    @staticmethod
    def validate_file_exists(path: Path, file_type: str = "file") -> None:
        """
        Validate that a file exists and is a file.
        
        Args:
            path: Path to validate
            file_type: Description of what this file is
            
        Raises:
            FileNotFoundError: If path doesn't exist
            IsADirectoryError: If path exists but is a directory
        """
        if not path.exists():
            raise FileNotFoundError(f"{file_type.capitalize()} not found: {path}")
        if path.is_dir():
            raise IsADirectoryError(f"Path exists but is a directory: {path}")
    
    @staticmethod
    def join_paths(*parts: str) -> Path:
        """
        Join path parts safely using pathlib instead of string concatenation.
        
        Example:
            join_paths("aisolutions-module", "component-backend") 
            -> Path("aisolutions-module/component-backend")
        """
        if not parts:
            return Path()
        
        result = Path(parts[0])
        for part in parts[1:]:
            result = result / part
        return result
    
    @staticmethod
    def find_files_by_pattern(directory: Path, pattern: str, recursive: bool = False) -> list[Path]:
        """
        Find files matching a pattern in a directory.
        
        Args:
            directory: Directory to search in
            pattern: Glob pattern (e.g., "*.py", "config.*")
            recursive: If True, search recursively using rglob
            
        Returns:
            List of matching file paths
        """
        if not directory.exists():
            return []
        
        if recursive:
            return sorted(directory.rglob(pattern))
        else:
            return sorted(directory.glob(pattern))
    
    @staticmethod
    def get_parent_containing_file(start_path: Path, filename: str, max_levels: int = 10) -> Optional[Path]:
        """
        Find the parent directory containing a specific file.
        
        Useful for finding project roots by looking for marker files like
        'samconfig.toml', 'pyproject.toml', etc.
        
        Args:
            start_path: Path to start searching from
            filename: Name of file to look for
            max_levels: Maximum number of parent directories to check
            
        Returns:
            Path to the parent directory containing the file, or None if not found
        """
        current = start_path
        for _ in range(max_levels):
            if (current / filename).exists():
                return current
            if current.parent == current:  # Reached root
                break
            current = current.parent
        return None
    
    def setup_python_path(self) -> None:
        """Add app directory to Python path for imports."""
        import sys
        
        # Try to detect current backend directory
        detected = self.detect_current_backend()
        if detected:
            app_or_component, backend_dir = detected
            app_parent = str(backend_dir)
            if app_parent not in sys.path:
                sys.path.insert(0, app_parent)