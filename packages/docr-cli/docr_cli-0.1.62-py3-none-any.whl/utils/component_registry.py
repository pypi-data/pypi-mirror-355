"""
Component and application registry.
Handles discovery, metadata, and validation of applications and components.
"""
from typing import Dict, Any, List


class ComponentRegistry:
    """Manages component and application discovery and metadata."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
    
    def discover_applications(self) -> List[str]:
        """Get list of configured applications."""
        return list(self.config_data.get('applications', {}).keys())
    
    def discover_components(self) -> List[str]:
        """Get list of configured components."""
        return list(self.config_data.get('components', {}).keys())
    
    def is_application(self, name: str) -> bool:
        """Check if name is an application."""
        return name in self.config_data.get('applications', {})
    
    def is_component(self, name: str) -> bool:
        """Check if name is a component."""
        return name in self.config_data.get('components', {})
    
    def get_component_metadata(self, component: str) -> Dict[str, Any]:
        """Get metadata for a specific component."""
        if component not in self.config_data.get('components', {}):
            raise ValueError(f"Unknown component: {component}")
        return self.config_data['components'][component]
    
    def get_app_directory_name(self, app_name: str) -> str:
        """Get the physical directory name for an application."""
        app_config = self.config_data['applications'].get(app_name, {})
        return app_config.get('directory_name', app_name)
    
    def get_app_from_directory_name(self, dir_name: str) -> str:
        """Get the logical application name from a directory name."""
        for app_name, app_config in self.config_data.get('applications', {}).items():
            if app_config.get('directory_name') == dir_name:
                return app_name
        return dir_name
    
    def get_component_npm_package(self, component: str) -> str:
        """Get npm package name for component."""
        return self.get_component_metadata(component)["npm_package"]
    
    def get_component_npm_alias(self, component: str) -> str:
        """Get npm alias for component."""
        return self.get_component_metadata(component)["npm_alias"]
    
    def get_component_client_name(self, component: str) -> str:
        """Get client name for verify_clients."""
        return self.get_component_metadata(component)["client_name"]
    
    def get_component_oidc_client_name(self, component: str) -> str:
        """Get OIDC client name for component."""
        return self.get_component_metadata(component)["oidc_client_name"]
    
    def get_application_oidc_client_name(self, app: str) -> str:
        """Get OIDC client name for application."""
        app_config = self.config_data['applications'].get(app, {})
        return app_config.get('oidc_client_name', app)
    
    def get_oidc_client_name(self, app_or_component: str) -> str:
        """Get OIDC client name for any app or component."""
        # Check if it's a component first
        if self.is_component(app_or_component):
            return self.get_component_oidc_client_name(app_or_component)
        
        # Check if it's an application
        if self.is_application(app_or_component):
            return self.get_application_oidc_client_name(app_or_component)
        
        # Fallback to simple name transformation
        return app_or_component.replace("-", "")
    
    def get_bootstrap_enabled_components(self) -> List[str]:
        """Get list of components that support bootstrap."""
        return [comp for comp, meta in self.config_data.get('components', {}).items() 
                if meta.get("bootstrap_supported", False)]
    
    def get_all_component_paths(self) -> Dict[str, str]:
        """Get all component frontend paths as relative strings."""
        paths = {}
        for component in self.discover_components():
            component_config = self.config_data['components'][component]
            paths[component] = component_config.get('frontend_path', '')
        return paths
    
    def get_all_component_npm_packages(self) -> Dict[str, str]:
        """Get all component npm package names."""
        return {comp: meta["npm_package"] 
                for comp, meta in self.config_data.get('components', {}).items()}
    
    def get_expected_modules(self) -> List[str]:
        """Get list of expected module directories for validation."""
        return self.config_data.get('expected_modules', {}).get('modules', [])
    
    def get_oidc_directory(self, oidc_component: str) -> str:
        """Get OIDC directory name for a component."""
        return self.config_data.get('oidc', {}).get('directories', {}).get(oidc_component)