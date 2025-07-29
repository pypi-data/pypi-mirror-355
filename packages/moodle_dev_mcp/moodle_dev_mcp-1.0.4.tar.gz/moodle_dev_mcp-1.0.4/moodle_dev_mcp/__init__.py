"""
Moodle Developer Documentation MCP Server

A Model Context Protocol (MCP) server that provides seamless access to Moodle
developer documentation from moodledev.io.
"""

__version__ = "1.0.3"
__author__ = "Khairu Aqsara"
__email__ = "wenkhairu@gmail.com"

from .server import main
import asyncio

def main_sync():
    """Synchronous entry point for console scripts."""
    asyncio.run(main())

__all__ = ["main", "main_sync"]
