"""Main entry point for the Billit MCP server."""

import logging
import os

from dotenv import load_dotenv

from .server import mcp

# Load environment variables
load_dotenv()

# Configure logging with safe fallback
def get_log_level():
    """Get log level with safe fallback for environment variable issues."""
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    
    # Handle shell-style variable expansion that wasn't processed
    if log_level_str.startswith("${") and log_level_str.endswith("}"):
        # Extract default value from ${VAR:-default} format
        if ":-" in log_level_str:
            log_level_str = log_level_str.split(":-")[1].rstrip("}")
        else:
            log_level_str = "INFO"
    
    # Validate it's a real logging level
    try:
        level = getattr(logging, log_level_str.upper())
        return level
    except AttributeError:
        # If not a valid logging level, default to INFO
        return logging.INFO

logging.basicConfig(
    level=get_log_level(),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()