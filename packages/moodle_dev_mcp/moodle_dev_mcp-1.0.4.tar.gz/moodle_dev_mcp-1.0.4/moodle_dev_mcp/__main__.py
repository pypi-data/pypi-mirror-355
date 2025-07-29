#!/usr/bin/env python3
"""
Main entry point for the moodle_dev_mcp package.

This allows the package to be executed as a module using:
python -m moodle_dev_mcp
"""

import asyncio
from .server import main

if __name__ == "__main__":
    asyncio.run(main())
