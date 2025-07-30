"""
Factory for creating API clients with proper environment setup.
This solves the issue of imports that depend on environment variables being set.
"""
# Standard library imports
from typing import TYPE_CHECKING
from typing import Any
from typing import Optional

# Type checking imports
if TYPE_CHECKING:
    from app.clients.cost_client import CostClient
    from app.clients.job_client import JobClient
    from app.clients.workspaces_client import WorkspacesClient


class ClientFactory:
    """Factory for creating configured API clients."""
    
    @staticmethod
    def create_cost_client() -> 'CostClient':
        """
        Create a CostClient instance.
        
        Environment variables must be set before calling this method:
        - COST_API_URL or COSTS_API_URL
        - COST_LAMBDA_FUNCTION_NAME (for direct invoke)
        
        Returns:
            Configured CostClient instance
        """
        # Import here after environment is configured
        from app.clients.cost_client import CostClient
        return CostClient()
    
    @staticmethod
    def create_job_client() -> 'JobClient':
        """
        Create a JobClient instance.
        
        Environment variables must be set before calling this method:
        - JOB_API_URL or JOBS_API_URL
        - JOB_LAMBDA_FUNCTION_NAME (for direct invoke)
        
        Returns:
            Configured JobClient instance
        """
        # Import here after environment is configured
        from app.clients.job_client import JobClient
        return JobClient()
    
    @staticmethod
    def create_workspaces_client() -> 'WorkspacesClient':
        """
        Create a WorkspacesClient instance.
        
        Environment variables must be set before calling this method:
        - WORKSPACES_API_URL
        - WORKSPACES_LAMBDA_FUNCTION_NAME (for direct invoke)
        
        Returns:
            Configured WorkspacesClient instance
        """
        # Import here after environment is configured
        from app.clients.workspaces_client import WorkspacesClient
        return WorkspacesClient()
    
    @staticmethod
    def create_sns_manager() -> Any:
        """
        Create an SNSManager instance.
        
        Environment variables must be set before calling this method:
        - SNS_TOPIC_ARN
        
        Returns:
            Configured SNSManager instance
        """
        # Import here after environment is configured
        from app.jobs.core.sns_manager import SNSManager
        return SNSManager()