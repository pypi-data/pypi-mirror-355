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

from ...app.logger import logger
from ...app.tool.base import BaseTool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

RED = "\033[91m"
RESET = "\033[0m"
GREEN = "\033[92m"


class Tool:
    """Represents a tool with its properties and formatting."""

    def __init__(self, name: str, description: str, input_schema: dict[str, Any]) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """Format tool information for LLM."""
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = (
                    f"- {param_name}: {param_info.get('description', 'No description')}"
                )
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)

        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""

class Server:
    """Manages MCP server connections and tool execution."""

    def __init__(self, name: str, config: dict[str, Any]) -> None:
        """
        Create a Server object, but don't start the session here.
        We'll do that in main() using an AsyncExitStack.
        """
        self.name: str = name
        self.config: dict[str, Any] = config
        self.session: ClientSession | None = None

    def attach_session(self, session: ClientSession) -> None:
        """Attach a pre-initialized session to this server."""
        self.session = session

    async def get_resources(self):
        """Get resources from the server."""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        resources = await self.session.list_resources()
        return resources

    async def list_tools(self) -> list[Any]:
        """List available tools from the server.

        Returns:
            A list of available tools.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        tools_response = await self.session.list_tools()
        tools = []

        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools.append(Tool(tool.name, tool.description, tool.inputSchema))
        return tools

    async def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        retries: int = 2,
        delay: float = 1.0,
    ) -> Any:
        """Execute a tool with a retry mechanism."""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        attempt = 0
        while attempt < retries:
            try:
               
                result = await self.session.call_tool(tool_name, arguments)

            
                result_dict = result.__dict__
                content = result_dict['content']
                text = content[0].__dict__['text']
                return text

            except Exception as e:
                attempt += 1

                logger.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                return "Error: " + str(e)
                # if attempt < retries:
                #     logger.info(f"Retrying in {delay} seconds...")
                #     await asyncio.sleep(delay)
                # else:
                #     logger.error("Max retries reached. Failing.")
                #     raise

    async def list_prompts(self) -> list[Any]:
        """List available prompts from the server.

        Returns:
            A list of available prompts.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        try:
            prompts = await self.session.list_prompts()
            return prompts
        except Exception as e:
            logger.error(f"Error listing prompts from {self.name}: {e}")
            raise

    async def use_prompt(self, prompt_name: str, arguments: dict[str, Any]) -> Any:
        """Use a prompt template with the provided arguments.

        Args:
            prompt_name: The name of the prompt to use
            arguments: Arguments to populate the prompt template

        Returns:
            The rendered prompt content
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        try:
            result = await self.session.get_prompt(prompt_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error using prompt {prompt_name} on {self.name}: {e}")
            raise

    async def sampling(self, request: dict[str, Any]) -> Any:
        """Use sampling capabilities of the server.

        Args:
            request: Sampling request parameters

        Returns:
            Sampling results
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        try:
            logger.info(f"{GREEN}Sampling on server {self.name}...{RESET}")
            result = await self.session.sampling(request)
            return result
        except Exception as e:
            logger.error(f"Error with sampling on {self.name}: {e}")
            raise

    async def list_roots(self) -> list[Any]:
        """List available roots from the server.

        Returns:
            A list of available roots.
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        try:
            roots = await self.session.list_roots()
            return roots
        except Exception as e:
            logger.error(f"Error listing roots from {self.name}: {e}")
            raise

    async def read_resource(self, resource_uri: str) -> Any:
        """Read a resource from the server.

        Args:
            resource_uri: URI of the resource to read

        Returns:
            Content of the resource
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")

        try:
            content = await self.session.read_resource(resource_uri)
            return content
        except Exception as e:
            logger.error(f"Error reading resource {resource_uri} from {self.name}: {e}")
            raise


class ServerToolAdapter(BaseTool):
    """
    Adapter class that wraps an MCP server tool, making it compatible with the Agent.
    This adapter creates a BaseTool that delegates calls to the corresponding MCP server tool.
    """

    def __init__(self, server, tool_name, description, input_schema):
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
            name=f"{server.name}_{tool_name}",
            description=f"[{server.name}] {description}",
            parameters=input_schema,
            server=server,  # Set the server in the model
        )

    async def execute(self, **kwargs):
        """Execute the tool by delegating to the server's execute_tool method."""
        tool_name = re.sub(f"^{re.escape(self.server.name)}_", "", self.name, count=1)
        try:
            # Pass the kwargs directly as the tool arguments
            result = await self.server.execute_tool(tool_name, kwargs)
            return result
        except Exception as e:
            logger.error(f"Error executing {tool_name} on {self.server.name}: {e}")
            return f"Error: {str(e)}"


class MCPTool(BaseTool):
    """
    Tool for interacting with MCP servers.

    This tool provides methods for interacting with MCP server capabilities
    including tools, resources, prompts, etc.

    To use this tool, always specify:
    1. An "action" parameter (what operation to perform)
    2. A "server_name" parameter (which server to target)

    To call a server tool:
    - Set "action" to "call_tool" (not the name of the tool)
    - Set "tool_name" to the actual name of the tool you want to call
    - Set "tool_args" to the arguments required by that tool

    Note: This tool assumes that MCP servers are already initialized in the runtime environment.
    It works with servers passed to it during instantiation or afterwards.
    """

    name: str = "mcp_tool"
    description: str = "Interact with Model Context Protocol (MCP) servers. Always use action='call_tool' when calling server tools."
    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "description": "The action to perform",
                "enum": [
                    "list_tools", "list_resources", "list_prompts",
                    "list_roots", "call_tool", "read_resource", "use_prompt",
                    "sampling"
                ]
            },
            "server_name": {
                "type": "string",
                "description": "Name of the server to target",
                "enum": [
                    "filesystem", "mongodb"
                ]
            },
            "tool_name": {
                "type": "string",
                "description": "Name of the tool to call"
            },
            "tool_args": {
                "type": "object",
                "description": "Arguments for the tool call"
            },
            "resource_uri": {
                "type": "string",
                "description": "URI of the resource to read"
            },
            "prompt_name": {
                "type": "string",
                "description": "Name of the prompt to use"
            },
            "prompt_args": {
                "type": "object",
                "description": "Arguments for the prompt"
            },
            "request": {
                "type": "object",
                "description": "Sampling request parameters"
            }
        },
        "required": ["action", "server_name"]
    }

    # Define servers as a Pydantic field
    servers: Dict[str, Any] = Field(default_factory=dict, exclude=True)

    def __init__(self, servers=None, **kwargs):
        """
        Initialize the MCP tool.

        Args:
            servers: Dictionary of Server objects that were initialized elsewhere
        """
        super().__init__(**kwargs)
        # Set servers using the defined Pydantic field
        self.servers = servers or {}



    async def list_tools(self, server_name: str) -> Dict[str, Any]:
        """
        List available tools from a specific MCP server.

        Args:
            server_name: Name of server to query

        Returns:
            List of available tools and their details
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        try:
            server = self.servers[server_name]
            tools = await server.list_tools()

            # Format tools for response
            formatted_tools = []
            for tool in tools:
                formatted_tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "server": server_name
                })

            return {
                "status": "success",
                "tools": formatted_tools,
                "server": server_name,
                "count": len(formatted_tools)
            }
        except Exception as e:
            logger.error(f"Error listing tools from {server_name}: {e}")
            return {"status": "error", "message": f"Error listing tools from {server_name}: {str(e)}"}

    async def list_resources(self, server_name: str) -> Dict[str, Any]:
        """
        List available resources from a specific MCP server.

        Args:
            server_name: Name of server to query

        Returns:
            List of available resources
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        try:
            server = self.servers[server_name]
            resources = await server.get_resources()

            # Process resources for response
            formatted_resources = []
            for resource in resources:
                # Add server name to each resource
                if isinstance(resource, dict):
                    resource_copy = dict(resource)
                    resource_copy["server"] = server_name
                    formatted_resources.append(resource_copy)
                else:
                    # Handle other formats as needed
                    formatted_resources.append({
                        "resource": str(resource),
                        "server": server_name
                    })

            return {
                "status": "success",
                "resources": formatted_resources,
                "server": server_name,
                "count": len(formatted_resources)
            }
        except Exception as e:
            logger.error(f"Error listing resources from {server_name}: {e}")
            return {"status": "error", "message": f"Error listing resources from {server_name}: {str(e)}"}

    async def call_tool(self, server_name: str, tool_name: str, tool_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on a specific MCP server.

        Args:
            server_name: Name of the server to use
            tool_name: Name of the tool to call
            tool_args: Arguments for the tool

        Returns:
            Result of the tool call
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        try:
            server = self.servers[server_name]
            result = await server.execute_tool(tool_name, tool_args)
            return {
                "status": "success",
                "result": result,
                "server": server_name
            }
        except Exception as e:
            logger.error(f"Error calling tool {tool_name} on {server_name}: {e}")
            return {"status": "error", "message": str(e), "server": server_name}

    async def list_prompts(self, server_name: str) -> Dict[str, Any]:
        """
        List available prompts from a specific MCP server.

        Args:
            server_name: Name of server to query

        Returns:
            List of available prompts
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        try:
            server = self.servers[server_name]
            prompts = await server.list_prompts()

            # Process prompts for response
            formatted_prompts = []
            for prompt in prompts:
                # Add server name to each prompt
                if isinstance(prompt, dict):
                    prompt_copy = dict(prompt)
                    prompt_copy["server"] = server_name
                    formatted_prompts.append(prompt_copy)
                else:
                    # Handle other formats as needed
                    formatted_prompts.append({
                        "prompt": str(prompt),
                        "server": server_name
                    })

            return {
                "status": "success",
                "prompts": formatted_prompts,
                "server": server_name,
                "count": len(formatted_prompts)
            }
        except Exception as e:
            logger.error(f"Error listing prompts from {server_name}: {e}")
            return {"status": "error", "message": f"Error listing prompts from {server_name}: {str(e)}"}

    async def list_roots(self, server_name: str) -> Dict[str, Any]:
        """
        List available roots from a specific MCP server.

        Args:
            server_name: Name of server to query

        Returns:
            List of available roots
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        try:
            server = self.servers[server_name]
            roots = await server.list_roots()

            # Process roots for response
            formatted_roots = []
            for root in roots:
                # Add server name to each root
                if isinstance(root, dict):
                    root_copy = dict(root)
                    root_copy["server"] = server_name
                    formatted_roots.append(root_copy)
                else:
                    # Handle other formats as needed
                    formatted_roots.append({
                        "root": str(root),
                        "server": server_name
                    })

            return {
                "status": "success",
                "roots": formatted_roots,
                "server": server_name,
                "count": len(formatted_roots)
            }
        except Exception as e:
            logger.error(f"Error listing roots from {server_name}: {e}")
            return {"status": "error", "message": f"Error listing roots from {server_name}: {str(e)}"}

    async def read_resource(self, server_name: str, resource_uri: str) -> Dict[str, Any]:
        """
        Read a resource from a specific MCP server.

        Args:
            server_name: Name of server to query
            resource_uri: URI of the resource to read

        Returns:
            Content of the resource
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        if not resource_uri:
            return {"status": "error", "message": "resource_uri is required"}

        try:
            server = self.servers[server_name]
            content = await server.read_resource(resource_uri)

            return {
                "status": "success",
                "content": content,
                "server": server_name
            }
        except Exception as e:
            logger.error(f"Error reading resource {resource_uri} from {server_name}: {e}")
            return {"status": "error", "message": str(e), "server": server_name}

    async def use_prompt(self, server_name: str, prompt_name: str, prompt_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use a prompt template from a specific MCP server.

        Args:
            server_name: Name of server to query
            prompt_name: Name of the prompt to use
            prompt_args: Arguments for the prompt

        Returns:
            Rendered prompt content
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        if not prompt_name:
            return {"status": "error", "message": "prompt_name is required"}

        try:
            server = self.servers[server_name]
            content = await server.use_prompt(prompt_name, prompt_args or {})

            return {
                "status": "success",
                "content": content,
                "server": server_name
            }
        except Exception as e:
            logger.error(f"Error using prompt {prompt_name} on {server_name}: {e}")
            return {"status": "error", "message": str(e), "server": server_name}

    async def sampling(self, server_name: str, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use sampling capabilities of a specific MCP server.

        Args:
            server_name: Name of server to query
            request: Sampling request parameters

        Returns:
            Sampling results
        """
        if not self.servers:
            return {"status": "error", "message": "No MCP servers available"}

        if server_name not in self.servers:
            return {"status": "error", "message": f"Server '{server_name}' not found"}

        try:
            server = self.servers[server_name]
            results = await server.sampling(request or {})

            return {
                "status": "success",
                "results": results,
                "server": server_name
            }
        except Exception as e:
            logger.error(f"Error with sampling on {server_name}: {e}")
            return {"status": "error", "message": str(e), "server": server_name}

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute an MCP operation.

        This is the main entry point for the tool. It dispatches to the appropriate method
        based on the action parameter.

        Args:
            action: The action to perform (list_tools, call_tool, etc.)
            server_name: The name of the server to target
            **kwargs: Additional arguments specific to the action

        Returns:
            Result of the operation
        """
        action = kwargs.get("action", "")
        server_name = kwargs.get("server_name", "")

      


        if not server_name:
            return {"status": "error", "message": "server_name is required"}

        if action == "list_tools":
            return await self.list_tools(server_name)

        elif action == "list_resources":
            return await self.list_resources(server_name)

        elif action == "list_prompts":
            return await self.list_prompts(server_name)

        elif action == "list_roots":
            return await self.list_roots(server_name)

        elif action == "call_tool":
            tool_name = kwargs.get("tool_name")
            tool_args = kwargs.get("tool_args", {})

            if not tool_name:
                return {"status": "error", "message": "tool_name is required"}

            return await self.call_tool(server_name, tool_name, tool_args)

        elif action == "read_resource":
            resource_uri = kwargs.get("resource_uri")

            if not resource_uri:
                return {"status": "error", "message": "resource_uri is required"}

            return await self.read_resource(server_name, resource_uri)

        elif action == "use_prompt":
            prompt_name = kwargs.get("prompt_name")
            prompt_args = kwargs.get("prompt_args", {})

            if not prompt_name:
                return {"status": "error", "message": "prompt_name is required"}

            return await self.use_prompt(server_name, prompt_name, prompt_args)

        elif action == "sampling":
            request = kwargs.get("request", {})

            return await self.sampling(server_name, request)

        else:
            return {
                "status": "error",
                "message": f"Action '{action}' not supported",
                "available_actions": [
                    "list_tools", "list_resources", "list_prompts",
                    "list_roots", "call_tool", "read_resource",
                    "use_prompt", "sampling"
                ]
            }

