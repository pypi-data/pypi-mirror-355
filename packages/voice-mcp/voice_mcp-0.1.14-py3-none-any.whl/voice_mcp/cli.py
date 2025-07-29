"""
CLI entry points for voice-mcp package.
"""

from .server import main as voice_mcp_main


def voice_mcp() -> None:
    """Entry point for voice-mcp command."""
    voice_mcp_main()


