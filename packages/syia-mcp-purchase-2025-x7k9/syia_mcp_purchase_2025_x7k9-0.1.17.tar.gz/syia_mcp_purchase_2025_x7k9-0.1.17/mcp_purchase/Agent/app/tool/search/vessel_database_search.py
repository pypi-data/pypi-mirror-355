import json
import uuid
from typing import Optional

import aiohttp
import asyncio

from app.tool.base import BaseTool, ToolResult
from app.logger import logger


class VesselDatabaseSearchTool(BaseTool):
    name: str = "vessel_database_search"
    description: str = """A deep database-level search tool for maritime vessel management.
This tool provides in-depth access to vessel database records when the standard internal search 
doesn't return sufficient results. Use this tool for:

1. Detailed technical specifications and history
2. Complete maintenance records and service history
3. Comprehensive crew and certification information
4. Detailed voyage data and performance metrics
5. Historical incident reports and resolutions

Only use this tool when the ship_management_internal_search tool doesn't provide the detailed information you need."""
    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The detailed database search query"
            }
        },
        "required": ["query"]
    }

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        if not query:
            return ToolResult(error="Query parameter is required")

        # Generate a unique session ID for this search
        task_id = str(uuid.uuid4())
        
        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 300 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "Content-Type": "application/json"
                }
                payload = {
                    "query": query,
                    "taskId": task_id
                }
                
                logger.info(f"Executing deep database search with query: '{query}' and taskId: {task_id}")
                
                try:
                    async with session.post(
                        "https://n8n.syia.ai/webhook/task_executer_open_manus",
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.text()
                            logger.info(f"Database search successful with {len(result)} characters")
                            try:
                                # Try to parse as JSON for better formatting
                                json_result = json.loads(result)
                                return ToolResult(output=json.dumps(json_result, indent=2))
                            except json.JSONDecodeError:
                                # If not valid JSON, return as plain text
                                return ToolResult(output=result)
                        else:
                            error_text = await response.text()
                            logger.error(f"Database API request failed with status {response.status}: {error_text}")
                            return ToolResult(error=f"Database search failed with status {response.status}: {error_text}")
                except aiohttp.ClientError as e:
                    logger.error(f"Network error during database API request: {str(e)}")
                    return ToolResult(error=f"Network error during database search: {str(e)}")
                except asyncio.TimeoutError:
                    logger.error("Database API request timed out after 20 seconds")
                    return ToolResult(error="Database search timed out after 20 seconds")

        except Exception as e:
            logger.error(f"Error during database search: {str(e)}")
            return ToolResult(error=f"Error during database search: {str(e)}") 