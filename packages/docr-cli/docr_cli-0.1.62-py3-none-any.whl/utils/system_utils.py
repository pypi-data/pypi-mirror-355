#!/usr/bin/env python3
"""
System utilities for CLI scripts.
Provides Docker verification and other system prerequisite checks.
"""
import subprocess
import shutil
from typing import Tuple


class SystemUtils:
    """System utility functions."""
    
    @staticmethod
    def verify_docker() -> Tuple[bool, str]:
        """
        Verify Docker is installed and running.
        
        Returns:
            Tuple of (is_available, message)
        """
        # Check if docker command exists
        if not shutil.which('docker'):
            return False, "❌ Docker not installed - Please install Docker Desktop"
        
        try:
            # Check if Docker daemon is running
            result = subprocess.run(
                ['docker', 'info'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Extract Docker version for verification message
                try:
                    version_result = subprocess.run(
                        ['docker', '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if version_result.returncode == 0:
                        version = version_result.stdout.strip()
                        return True, f"Docker running - {version}"
                    else:
                        return True, "Docker running"
                except Exception:
                    return True, "✅ Docker running"
            else:
                return False, "❌ Docker daemon not running - Please start Docker Desktop"
                
        except subprocess.TimeoutExpired:
            return False, "❌ Docker daemon not responding - Please restart Docker Desktop"
        except Exception as e:
            return False, f"❌ Docker check failed: {e}"
    
    @staticmethod
    def verify_command_exists(command: str) -> Tuple[bool, str]:
        """
        Verify a command exists on the system.
        
        Args:
            command: Command name to check
            
        Returns:
            Tuple of (exists, message)
        """
        if shutil.which(command):
            try:
                # Try to get version for additional info
                result = subprocess.run(
                    [command, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]  # First line only
                    return True, f"✅ {command} available - {version}"
                else:
                    return True, f"✅ {command} available"
            except Exception:
                return True, f"✅ {command} available"
        else:
            return False, f"❌ {command} not installed"
    
    @staticmethod
    def verify_python_packages(packages: list) -> Tuple[bool, str]:
        """
        Verify Python packages are available.
        
        Args:
            packages: List of package names to check
            
        Returns:
            Tuple of (all_available, message)
        """
        missing_packages = []
        
        for package in packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return False, f"❌ Missing Python packages: {', '.join(missing_packages)}"
        else:
            return True, f"✅ All required Python packages available ({len(packages)} packages)"
    
    @staticmethod
    def get_system_info() -> dict:
        """
        Get basic system information.
        
        Returns:
            Dictionary with system info
        """
        import platform
        import sys
        
        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'python_version': sys.version.split()[0],
            'python_executable': sys.executable
        }