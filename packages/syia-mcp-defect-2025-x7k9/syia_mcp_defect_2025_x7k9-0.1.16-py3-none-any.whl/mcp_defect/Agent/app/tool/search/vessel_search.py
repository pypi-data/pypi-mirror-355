import json
from typing import Any, Dict, Optional

import aiohttp
from pydantic import BaseModel
import asyncio

from app.tool.base import BaseTool, ToolResult


class ShipManagementInternalKnowledgeTool(BaseTool):
    name: str = "ship_management_internal_search"
    description: str = """A comprehensive internal knowledge search tool for ship management that provides access to:
1. PMS (Planned Maintenance System) data:
   - Maintenance schedules, work orders, equipment history, spare parts

2. Financial and Administrative data:
   - Budget, accounts, cost tracking, purchase orders

3. Documentation and Reports:
   - Vessel reports, manuals, technical docs, compliance records, SOPs

4. Communication and Correspondence:
   - Internal emails, captain's reports, department communications, meeting minutes

5. Vendor Management:
   - Registered suppliers, approved lists, performance records, contracts

This tool searches exclusively within the company's internal knowledge base, including ERP system, emails, and internal documentation. For external information (weather, port schedules, etc.), use the web search tools."""
    parameters: Optional[dict] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The internal knowledge query to search for"
            }
        },
        "required": ["query"]
    }

    async def execute(self, **kwargs) -> ToolResult:
        query = kwargs.get("query")
        if not query:
            return ToolResult(error="Query parameter is required")

        try:
            timeout = aiohttp.ClientTimeout(total=300)  # 300 second timeout
            async with aiohttp.ClientSession(timeout=timeout) as session:
                headers = {
                    "Content-Type": "application/json"
                }
                payload = {
                    "query": query
                }
                
                try:
                    async with session.post(
                        "https://ranking.syia.ai/search",
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            return ToolResult(output=json.dumps(result, indent=2))
                        else:
                            error_text = await response.text()
                            return ToolResult(error=f"API request failed with status {response.status}: {error_text}")
                except aiohttp.ClientError as e:
                    return ToolResult(error=f"Network error during API request: {str(e)}")
                except asyncio.TimeoutError:
                    return ToolResult(error="API request timed out after 10 seconds")

        except Exception as e:
            return ToolResult(error=f"Error during internal knowledge search: {str(e)}")

    async def think(self, **kwargs) -> str:
        # This method is not implemented in the original file or the new one
        # It's kept empty as it's not required in the new implementation
        return ""

    async def process(self, **kwargs) -> ToolResult:
        # This method is not implemented in the original file or the new one
        # It's kept empty as it's not required in the new implementation
        return ToolResult(output="") 