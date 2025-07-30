#!/usr/bin/env python3
"""
JWT token handling utilities for CLI scripts.
Provides token decoding, validation, and information extraction.
"""
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
from rich.table import Table
import jwt


class JWTUtils:
    """JWT token handling utilities."""
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode JWT token without verification.
        
        Args:
            token: JWT token string (with or without Bearer prefix)
            
        Returns:
            Dict with header, payload, and signature
            
        Raises:
            ValueError: If token format is invalid
        """
        # Remove Bearer prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        elif ":" in token:
            # Handle OIDC_USER_JWT format
            token = token.split(":", 1)[1]
        
        # Decode without verification (we don't have the public key)
        try:
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            return {
                "header": header,
                "payload": payload,
                "signature": token.split('.')[2] if '.' in token else ""
            }
        except jwt.DecodeError as e:
            raise ValueError(f"Invalid JWT format: {str(e)}")
    
    
    @staticmethod
    def check_expiry(token: str) -> Tuple[bool, int]:
        """
        Check if token is expired and time remaining.
        
        Args:
            token: JWT token string
            
        Returns:
            Tuple of (is_valid, seconds_remaining)
            If expired, seconds_remaining will be negative
        """
        try:
            # Clean up the token - remove Bearer prefix and OIDC_USER_JWT prefix
            if token.startswith("Bearer "):
                token = token[7:]
            if "OIDC_USER_JWT:" in token:
                token = token.split("OIDC_USER_JWT:")[1]
            
            # Decode without verification
            payload = jwt.decode(token, options={"verify_signature": False})
            
            if 'exp' not in payload:
                return True, 0  # No expiry
            
            exp_time = payload['exp']
            current_time = int(time.time())
            time_remaining = exp_time - current_time
            
            return time_remaining > 0, time_remaining
            
        except Exception as e:
            # Token decode failed
            return False, 0
    
    @staticmethod
    def extract_client_id(token: str) -> Optional[str]:
        """
        Extract client ID from token.
        
        Args:
            token: JWT token string
            
        Returns:
            Client ID or None if not found
        """
        try:
            # Clean up the token - remove Bearer prefix and OIDC_USER_JWT prefix
            if token.startswith("Bearer "):
                token = token[7:]
            if "OIDC_USER_JWT:" in token:
                token = token.split("OIDC_USER_JWT:")[1]
            
            # Decode without verification
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload.get('aud')
        except Exception:
            return None
    
    @staticmethod
    def format_time_remaining(seconds: int) -> str:
        """Format seconds into human-readable time."""
        if seconds < 0:
            return "Expired"
        
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @staticmethod
    def format_token_info(token: str) -> Table:
        """
        Create Rich table with token information.
        
        Args:
            token: JWT token string
            
        Returns:
            Rich Table with token details
        """
        table = Table(title="Token Information")
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        
        try:
            # Clean up the token - remove Bearer prefix and OIDC_USER_JWT prefix
            if token.startswith("Bearer "):
                token = token[7:]
            if "OIDC_USER_JWT:" in token:
                token = token.split("OIDC_USER_JWT:")[1]
            
            # Use PyJWT to decode without verification
            header = jwt.get_unverified_header(token)
            payload = jwt.decode(token, options={"verify_signature": False})
            
            # Header info
            table.add_row("Algorithm", header.get('alg', 'Unknown'))
            table.add_row("Key ID", header.get('kid', 'Unknown'))
            
            # Basic info
            table.add_row("Issuer", payload.get('iss', 'Unknown'))
            table.add_row("Subject", payload.get('sub', 'Unknown'))
            table.add_row("Client ID", payload.get('aud', 'Unknown'))
            
            # User info
            if 'email' in payload:
                table.add_row("Email", payload['email'])
            if 'preferred_username' in payload:
                table.add_row("Username", payload['preferred_username'])
            if 'name' in payload:
                table.add_row("Name", payload['name'])
            
            # Entitlements
            if 'entitlements' in payload:
                entitlements = payload['entitlements']
                # Format entitlements nicely
                admin_entitlements = []
                writer_entitlements = []
                for ent in entitlements:
                    if ent.endswith(':admins'):
                        admin_entitlements.append(ent.split(':')[-2])
                    elif ':writers' in ent:
                        writer_entitlements.append(ent.split(':')[-2])
                
                if admin_entitlements:
                    table.add_row("Admin For", ", ".join(admin_entitlements))
                if writer_entitlements:
                    table.add_row("Writer For", ", ".join(writer_entitlements))
            
            # Time info
            current_time = int(time.time())
            
            if 'iat' in payload:
                iat = payload['iat']
                issued_ago = (current_time - iat) // 60
                issued_dt = datetime.fromtimestamp(iat)
                table.add_row("Issued", f"{issued_dt.strftime('%Y-%m-%d %H:%M:%S')} ({issued_ago} minutes ago)")
            
            if 'exp' in payload:
                exp = payload['exp']
                time_remaining = exp - current_time
                exp_datetime = datetime.fromtimestamp(exp)
                
                if time_remaining > 0:
                    hours = time_remaining // 3600
                    minutes = (time_remaining % 3600) // 60
                    table.add_row("Expires", f"{exp_datetime.strftime('%Y-%m-%d %H:%M:%S')} [green]({hours}h {minutes}m remaining)[/green]")
                else:
                    expired_ago = abs(time_remaining) // 60
                    table.add_row("Expires", f"{exp_datetime.strftime('%Y-%m-%d %H:%M:%S')} [red](EXPIRED {expired_ago}m ago)[/red]")
            
        except Exception as e:
            table.add_row("Error", f"[red]{str(e)}[/red]")
            # Add debug info
            table.add_row("Debug", f"Token length: {len(token)} chars")
            table.add_row("Debug", f"First 50 chars: {token[:50]}..." if len(token) > 50 else f"Token: {token}")
        
        return table
    
    @staticmethod
    def validate_token_format(token: str) -> bool:
        """
        Validate if token has correct format.
        
        Args:
            token: Token string to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Check for OIDC_USER_JWT format
        if token.startswith("Bearer OIDC_USER_JWT:"):
            token = token.split(":", 1)[1]
        elif token.startswith("Bearer "):
            token = token[7:]
        
        # Check JWT structure
        parts = token.split('.')
        return len(parts) == 3
    
    @staticmethod
    def get_token_type(token: str) -> str:
        """
        Determine token type from format.
        
        Returns:
            'user' for user JWT, 'jwt' for standard JWT tokens, 'unknown' otherwise
        """
        if "OIDC_USER_JWT" in token:
            return "user"
        elif token.count('.') == 2:
            return "jwt"
        else:
            return "unknown"