import os
import shutil
import asyncio
import json
import re
from typing import Dict, List, Any, Optional, Union
from contextlib import AsyncExitStack
from pathlib import Path
from colorama import Fore, Style
from pydantic import Field

import json

from ..app.logger import logger
from ..app.tool.base import BaseTool
import sys
sys.path.append("../../../")  # Ensure the parent directory is in sys.path for import
from ...tools import handle_call_tool

class ServerToolAdapter(BaseTool):
    """
    Adapter class that wraps an MCP server tool, making it compatible with the Agent.
    This adapter creates a BaseTool that delegates calls to the corresponding MCP server tool.
    """

    def __init__(self, tool_name, description, input_schema):
        """
        Initialize the adapter with the server and tool details.

        Args:
            server: The MCP server instance
            tool_name: The name of the tool on the server
            description: The tool's description
            input_schema: The tool's input schema
        """
        # Initialize the BaseTool with all required fields
        super().__init__(
            name=tool_name,
            description=description,
            parameters=input_schema,
        )

    async def execute(self, **kwargs):
        """Execute the tool by delegating to handle_call_tool from tools.py."""
        tool_name = self.name
        try:
            # Use handle_call_tool for execution
            result = await handle_call_tool(tool_name, kwargs)
            if result:
                # If the result is a list, extract the first item
                if isinstance(result[0], dict):
                    content = result[0].get("text", "")
    
                else:    
                    content = result[0].__dict__['text']
            else:
                content = ""
            return content
        except Exception as e:
            logger.error(f"Error executing {tool_name} using handle_call_tool: {e}")
            return f"Error: {str(e)}"




