"""
WATI MCP Server - A Model Context Protocol server for WhatsApp Business API integration.

This package provides MCP tools for interacting with the WATI WhatsApp Business API,
allowing AI assistants to send messages, manage contacts, and retrieve conversation data.
"""

__version__ = "0.1.1"
__author__ = "Jairaj Mehra"
__description__ = "MCP Server for WATI WhatsApp Business API"

from .server import create_server

__all__ = ["create_server", "__version__"] 