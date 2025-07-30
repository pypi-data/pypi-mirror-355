#!/usr/bin/env python3
"""
Shared console singleton for Rich output across all CLI commands.
This prevents "Only one live display may be active at once" errors.
"""
import os
from rich.console import Console
from typing import Optional


class SharedConsole:
    """Singleton console instance shared across all CLI commands."""
    
    _instance: Optional[Console] = None
    
    @classmethod
    def get_console(cls) -> Console:
        """Get or create the shared console instance."""
        if cls._instance is None:
            # Check if we're running as a subprocess
            is_subprocess = os.environ.get("DOCR_SUBPROCESS", "false").lower() == "true"
            
            if is_subprocess:
                # Create a console for subprocess mode - show ALL output for debugging
                # Use NO_COLOR to avoid ANSI escape codes in subprocess output
                cls._instance = Console(
                    force_terminal=False,  # Don't force terminal mode in subprocess
                    force_interactive=False,  # Disable interactive features
                    quiet=False,  # Show ALL status messages for ultra-verbose output
                    stderr=False,  # Output to stdout
                    no_color=True,  # Disable colors to avoid ANSI codes
                    width=120  # Set a reasonable width
                )
            else:
                # Create normal Rich console
                cls._instance = Console()
        
        return cls._instance
    
    @classmethod
    def reset(cls):
        """Reset the console instance (mainly for testing)."""
        cls._instance = None


def get_shared_console() -> Console:
    """Convenience function to get the shared console."""
    return SharedConsole.get_console()


def safe_print(*args, **kwargs):
    """
    Safe print function that works in both normal and subprocess mode.
    Falls back to regular print if Rich console fails.
    """
    try:
        console = get_shared_console()
        console.print(*args, **kwargs)
    except Exception:
        # Fallback to regular print, stripping Rich markup
        import re
        text = ' '.join(str(arg) for arg in args)
        # Strip Rich markup tags
        text = re.sub(r'\[/?\w+\]', '', text)
        print(text)