#!/usr/bin/env python3
"""
API URL utilities for resolving and validating API endpoints.
"""
from typing import Optional


def get_api_url_for_service(
    service: str,
    console_utils,
    stage: str = "sandbox",
    show_info: bool = False,
    show_supported_endpoints: bool = False
) -> str:
    """
    Get the API URL for a specific service (application or component).
    
    Args:
        service: The service name (e.g., 'legislative-review', 'cost', 'jobs')
        console_utils: Console utilities instance for printing messages
        stage: The deployment stage (sandbox, dev, qa, prod)
        show_info: Whether to print info message showing the URL being used
        show_supported_endpoints: Whether to show supported endpoints in error message
        
    Returns:
        The API URL for the service
        
    Raises:
        SystemExit: If the URL cannot be found or configuration is invalid
    """
    try:
        from . import AppConfig
        url = AppConfig.get_api_url(service, stage)
        
        if not url:
            error_msg = (
                f"No API URL found for {service} in configuration.\n"
                f"Run 'docr refresh' to update configuration from AWS."
            )
            
            if show_supported_endpoints:
                applications = AppConfig.discover_applications()
                components = AppConfig.discover_components()
                supported_endpoints = applications + components
                error_msg += f"\nSupported endpoints: {', '.join(supported_endpoints)}"
            
            console_utils.print_error(error_msg, exit_code=1)
        
        # Ensure URL ends with /api for component endpoints (not main application)
        if not AppConfig.is_application(service) and not url.endswith('/api'):
            url = url.rstrip('/') + '/api'
        
        if show_info:
            console_utils.print_info(f"Using API URL for {service}: {url}")
        
        return url
        
    except Exception as e:
        console_utils.print_error(
            f"Failed to load configuration: {str(e)}",
            exit_code=1
        )