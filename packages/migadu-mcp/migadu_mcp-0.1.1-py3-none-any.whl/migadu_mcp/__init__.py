"""
Migadu MCP Server

A FastMCP server for managing Migadu mailboxes, identities, forwardings, aliases, and rewrites.
"""

__version__ = "0.1.1"
__author__ = "Michael Broell"
__email__ = "michaeljbroel@gmail.com"

from .main import mcp

__all__ = ["mcp"]