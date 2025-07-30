"""
Step 3: Credential Storage
- Store client secrets in UMD credential store
- Clean up old credentials
"""
import os
from utils import ConsoleUtils, OIDCConfigManager
from utils.shared_console import get_shared_console


class CredentialStorageStep:
    """Handle credential storage for OIDC clients."""
    
    def __init__(self):
        self.console = get_shared_console()
        self.console_utils = ConsoleUtils()
    
    def cleanup_old_credentials(self, app: str, dev_initials: str):
        """Clean up old credential store entries for this app."""
        try:
            from utils.umd_credential_store import delete_credential
            
            # Set up environment for credential store using consolidated utility
            OIDCConfigManager.setup_oidc_credential_store_env(dev_initials, "sandbox")
            
            # Get secret key from config
            from utils import AppConfig
            config = AppConfig.load_config()
            
            # Check if it's an application or component
            if app in config.get('applications', {}):
                key = config['applications'][app].get('secret_key')
            elif app in config.get('components', {}):
                key = config['components'][app].get('secret_key')
            else:
                key = None
                
            if not key:
                raise ValueError(f"No secret_key defined in config for {app}")
            
            # Try to delete any existing credential
            try:
                delete_credential(key)
                self.console.print(f"    ✓ Removed old credential: {key}")
            except Exception as e:
                # Credential didn't exist or delete failed, which is fine
                if "not found" not in str(e).lower():
                    self.console.print(f"    ⚠ Could not remove old credential: {e}")
                    
        except Exception as e:
            # Non-critical error, just log it
            self.console.print(f"    ⚠ Credential cleanup failed: {e}")
    
    def store_client_secret(self, app: str, secret: str, stage: str, dev_initials: str) -> bool:
        """Store client secret in credential store. Returns True if successful."""
        # Clean up old credentials first
        self.cleanup_old_credentials(app, dev_initials)
        
        # Use the UMD credential store utility
        from utils.umd_credential_store import add_credential
        
        self.console.print("  → Storing client secret in UMD credential store...")
        
        try:
            # Set up environment for credential store using consolidated utility
            OIDCConfigManager.setup_oidc_credential_store_env(dev_initials, stage)
            
            # Get secret key from config
            from utils import AppConfig
            config = AppConfig.load_config()
            
            # Check if it's an application or component
            if app in config.get('applications', {}):
                key = config['applications'][app].get('secret_key')
            elif app in config.get('components', {}):
                key = config['components'][app].get('secret_key')
            else:
                key = None
                
            if not key:
                raise ValueError(f"No secret_key defined in config for {app}")
                
            add_credential(key, secret, force=True)  # Added force=True to overwrite existing
            return True
            
        except Exception as e:
            self.console.print(f"  ⚠ Failed to store client secret: {e}")
            return False