"""
Project-level configuration management.
Handles project root, active app, developer initials.
"""
# Standard library imports
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import Dict

# Third-party imports
import tomli_w
import tomllib

# Type checking imports
if TYPE_CHECKING:
    from .app_config import AppConfig


class ProjectConfig:
    """Manages core project configuration."""
    
    def __init__(self, config_data: Dict[str, Any]):
        self.config_data = config_data
    
    def get_project_root(self) -> Path:
        """Get project root directory from configuration."""
        project_root = Path(self.config_data['project']['root'])
        
        if not project_root.exists():
            raise RuntimeError(
                f"Configured project root does not exist: {project_root}\n"
                "Please run 'docr setup' to reconfigure."
            )
        
        return project_root
    
    
    def get_developer_initials(self) -> str:
        """Get developer initials from project config."""
        return self.config_data['project']['developer_initials']
    
    def get_app_info(self) -> Dict[str, Any]:
        """Get application configuration information for display."""
        # Import here to avoid circular dependency at module load time
        from .app_config import AppConfig
        
        return {
            'project_root': self.config_data['project']['root'],
            'last_updated': self.config_data['project'].get('last_updated', 'Never'),
            'config_file': str(AppConfig.CONFIG_FILE),
            'developer_initials': self.get_developer_initials(),
            'available_applications': list(self.config_data.get('applications', {}).keys()),
            'available_components': list(self.config_data.get('components', {}).keys())
        }
    
