"""OIDC verification implementation."""
from .base import BaseDoctorCheck
from oidc.verification import VerificationStep
from utils import AppConfig
from utils.api_gateway_utils import APIGatewayUtils


class OIDCDoctor(BaseDoctorCheck):
    """Verify OIDC system configuration."""
    
    def check(self) -> bool:
        """Verify OIDC client registrations and setup."""
        from rich.text import Text
        
        
        # Enhanced step header
        step_text = Text()
        step_text.append("🔍 ", style="")
        step_text.append("Checking OIDC System", style="bold cyan")
        
        self.console_utils.console.print(step_text)
        self.console_utils.console.print()
        
        # Reuse existing verification logic from oidc/verification.py
        verification_step = VerificationStep()
        
        config = AppConfig.load_config()
        apps_to_verify = []
        
        # Get applications that should have OIDC clients
        if 'applications' in config:
            apps_to_verify.extend(config['applications'].keys())
        
        # Discover APIs once for all verifications with better output
        try:
            discovered_apis = APIGatewayUtils.get_all_api_gateway_ids(self.stage)
            api_text = Text()
            api_text.append("🔌 ", style="")
            api_text.append(f"Found {len(discovered_apis)} API Gateways", style="dim")
            self.console_utils.console.print(api_text)
        except Exception as e:
            self.console_utils.print_error(f"Failed to discover APIs: {str(e)}")
            discovered_apis = {}
        
        overall_success = True
        
        # Set up environment for OIDC operations
        from utils import OIDCConfigManager
        dev_initials = AppConfig.get_developer_initials()
        
        # First, run overall pattern consistency check with better styling
        from rich.text import Text
        
        pattern_text = Text()
        pattern_text.append("\n🔍 ", style="")
        pattern_text.append("Running OIDC pattern consistency check", style="bold blue")
        self.console_utils.console.print(pattern_text)
        
        # Run simplified pattern consistency check for doctor
        try:
            pattern_success = verification_step.verify_oidc_pattern_consistency_simple(self.stage)
        except RuntimeError as e:
            if "Could not detect application from current directory" in str(e):
                self.log_result(
                    "OIDC Pattern Consistency",
                    False,
                    "OIDC verification must be run from within an application directory (e.g., legislative-review-backend)"
                )
                pattern_success = False
                overall_success = False
            else:
                raise
        
        if pattern_success:
            self.log_result(
                "OIDC Pattern Consistency", 
                True,
                "Pattern consistency verified"
            )
        
        for app_name in apps_to_verify:
            # Enhanced app verification header
            app_text = Text()
            app_text.append(f"\n📝 ", style="")
            app_text.append(f"Verifying {app_name}", style="bold yellow")
            self.console_utils.console.print(app_text)
            
            if self.verbose:
                self.console_utils.console.print("─" * 30, style="dim")
            
            try:
                # Set up credential store environment for this app
                try:
                    OIDCConfigManager.setup_oidc_credential_store_env(dev_initials, self.stage)
                except Exception as e:
                    if self.verbose:
                        self.console_utils.print_warning(f"  Could not set up credential store env: {str(e)}")
                
                # Use existing verification logic but capture results
                # We'll use a monkey patch approach to capture the verification results
                # since verify_single_registration prints directly
                original_print_info = verification_step.console_utils.print_info
                original_print_error = verification_step.console_utils.print_error
                original_print_success = verification_step.console_utils.print_success
                
                # Capture verification output
                verification_output = []
                
                def capture_print(msg):
                    verification_output.append(msg)
                    if self.verbose:
                        original_print_info(msg)
                
                # Temporarily replace print methods
                verification_step.console_utils.print_info = capture_print
                verification_step.console_utils.print_error = capture_print
                verification_step.console_utils.print_success = capture_print
                
                try:
                    app_success = verification_step.verify_single_registration_simple(
                        app_name, 
                        self.stage, 
                        show_header=False,
                        discovered_apis=discovered_apis
                    )
                except RuntimeError as e:
                    if "Could not detect application from current directory" in str(e):
                        app_success = False
                        verification_output.append(f"OIDC verification must be run from within an application directory")
                    else:
                        raise
                finally:
                    # Restore original methods
                    verification_step.console_utils.print_info = original_print_info
                    verification_step.console_utils.print_error = original_print_error
                    verification_step.console_utils.print_success = original_print_success
                
                # Parse verification output to get specific results
                checks_passed = self._parse_verification_output(verification_output)
                
                if app_success:
                    self.log_result(
                        f"{app_name} OIDC setup",
                        True,
                        f"All OIDC checks passed ({checks_passed})"
                    )
                else:
                    if "must be run from within an application directory" in str(verification_output):
                        self.log_result(
                            f"{app_name} OIDC setup",
                            False,
                            f"OIDC verification must be run from within an application directory"
                        )
                    else:
                        self.log_result(
                            f"{app_name} OIDC setup",
                            False,
                            f"OIDC verification failed ({checks_passed})"
                        )
                    overall_success = False
                    
            except Exception as e:
                self.log_result(
                    f"{app_name} OIDC setup",
                    False,
                    f"Error during verification: {str(e)}"
                )
                overall_success = False
        
        return overall_success
    
    def _parse_verification_output(self, output_lines):
        """Parse verification output to extract check counts."""
        # Look for our new "Overall:" pattern first
        for line in reversed(output_lines):
            if "overall:" in line.lower():
                import re
                match = re.search(r'(\d+)/(\d+)', line)
                if match:
                    return f"{match.group(1)}/{match.group(2)} checks"
        
        # Look for other patterns like "ALL CHECKS PASSED (5/5)"
        for line in reversed(output_lines):
            if "checks passed" in line.lower():
                import re
                match = re.search(r'(\d+)/(\d+)', line)
                if match:
                    return f"{match.group(1)}/{match.group(2)} checks"
        
        # Count checkmarks and X marks as fallback
        passed = sum(1 for line in output_lines if '✅' in line)
        failed = sum(1 for line in output_lines if '❌' in line)
        total = passed + failed
        
        if total > 0:
            return f"{passed}/{total} checks"
        return "unknown"