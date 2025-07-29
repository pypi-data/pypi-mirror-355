"""
CLI entry points for voice-mcp package.

These functions execute the UV scripts with proper path resolution.
"""

import subprocess
import sys
from pathlib import Path


def get_script_path(script_name: str) -> Path:
    """Get the full path to a script in the package."""
    return Path(__file__).parent / "scripts" / script_name


def run_uv_script(script_name: str) -> None:
    """Run a UV script with the given name."""
    script_path = get_script_path(script_name)
    
    if not script_path.exists():
        print(f"Error: Script '{script_name}' not found at {script_path}", file=sys.stderr)
        sys.exit(1)
    
    # Run the script with UV, passing along any command line arguments
    cmd = ["uv", "run", "--script", str(script_path)] + sys.argv[1:]
    
    try:
        result = subprocess.run(cmd)
        sys.exit(result.returncode)
    except FileNotFoundError:
        print("Error: 'uv' command not found. Please install uv: https://github.com/astral-sh/uv", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error running script: {e}", file=sys.stderr)
        sys.exit(1)


def voice_mcp() -> None:
    """Entry point for voice-mcp command."""
    run_uv_script("voice-mcp")


