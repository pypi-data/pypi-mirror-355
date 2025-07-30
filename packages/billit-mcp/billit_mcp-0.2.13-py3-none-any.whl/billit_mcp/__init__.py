"""Billit MCP Server - Model Context Protocol server for Billit API integration."""

from .server import mcp

def main():
    """Main entry point for the billit-mcp script."""
    mcp.run()

__all__ = ["mcp", "main"]