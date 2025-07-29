"""Claude Commander - Alias package for claude-command."""

# Re-export everything from claude-command
try:
    # Import the main function from the claude-command package
    from claude_command.server import main
    
    # Re-export for console script compatibility
    __all__ = ['main']
    
except ImportError as e:
    raise ImportError(
        "claude-command package is required but not installed. "
        "This should not happen if installed via pip/uvx. "
        f"Original error: {e}"
    ) from e