"""
Namespace alias for claude-command.

This package is a namespace holder that redirects to the main claude-command package.
Install claude-command directly for the actual functionality.
"""

# Re-export everything from the main package
from claude_command import *

__version__ = "0.2.1"
__all__ = ["*"]