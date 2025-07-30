"""
Namespace alias for claude-command.

This package is a namespace holder that redirects to the main claude-command package.
Install claude-command directly for the actual functionality.
"""

# Re-export everything from the main package
try:
    from claude_command import *  # noqa: F403, F401
except ImportError:
    pass  # Package will be installed when this alias is installed

from importlib.metadata import version

__version__ = version("claude-command")
