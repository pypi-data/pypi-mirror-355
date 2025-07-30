"""
Credential Manager MCP Server

A FastMCP server for securely managing API credentials locally through the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"

from .server import main

__all__ = ["main"] 