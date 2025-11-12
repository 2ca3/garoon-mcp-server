#!/usr/bin/env python3
"""Garoon MCP Server

A Model Context Protocol (MCP) server for Garoon API integration.
Uses X-Cybozu-Authorization header with Base64 encoded credentials.
"""

import asyncio
import logging
import sys
from typing import Optional, Dict, Any, List
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
)
from garoon_client import GaroonClient

# Configure logging to use stderr to avoid interfering with MCP JSON-RPC on stdout
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(name)s: %(message)s')
logger = logging.getLogger(__name__)

# Also configure garoon_client logger to use stderr
garoon_logger = logging.getLogger("garoon_client")
garoon_logger.setLevel(logging.INFO)

class GaroonMCPServer:
    def __init__(self) -> None:
        self.server = Server("garoon-mcp")
        self.garoon_client: Optional[GaroonClient] = None

    async def initialize(self, base_url: str, g_username: str, g_password: str) -> None:
        """Initialize Garoon client connection using X-Cybozu-Authorization header"""
        try:
            self.garoon_client = GaroonClient(base_url, g_username, g_password)
            await self.garoon_client.authenticate()
            logger.info("Garoon client initialized successfully with X-Cybozu-Authorization header")
        except Exception as e:
            logger.error(f"Failed to initialize Garoon client: {e}")
            raise

    def setup_handlers(self) -> None:
        """Setup MCP tool handlers"""

        @self.server.list_resources()
        async def list_resources() -> List[Any]:
            """List available resources"""
            return []

        @self.server.list_prompts()
        async def list_prompts() -> List[Any]:
            """List available prompts"""
            return []
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Garoon tools"""
            return [
                Tool(
                    name="get_schedule",
                    description="Get schedule events from Garoon for yourself or other users",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "start_date": {
                                "type": "string",
                                "description": "Start date (YYYY-MM-DD format)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date (YYYY-MM-DD format)"
                            },
                            "user_id": {
                                "type": "string",
                                "description": "User ID to get schedule for. If not specified, returns your own schedule. Use search_users tool to find user IDs."
                            }
                        },
                        "required": ["start_date", "end_date"]
                    }
                ),
                Tool(
                    name="create_schedule",
                    description="Create a new schedule event in Garoon",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Event subject/title"
                            },
                            "start_datetime": {
                                "type": "string",
                                "description": "Start datetime (ISO format)"
                            },
                            "end_datetime": {
                                "type": "string",
                                "description": "End datetime (ISO format)"
                            },
                            "description": {
                                "type": "string",
                                "description": "Event description (optional)"
                            }
                        },
                        "required": ["subject", "start_datetime", "end_datetime"]
                    }
                ),
                Tool(
                    name="search_users",
                    description="Search for users in Garoon by name or other criteria",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query (user name, email, etc.)"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results to return",
                                "default": 20
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="find_available_time",
                    description="Find available time slots for a meeting with another user",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_id": {
                                "type": "string",
                                "description": "Other user's Garoon user ID"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Search start date (YYYY-MM-DD format)"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "Search end date (YYYY-MM-DD format)"
                            },
                            "duration_minutes": {
                                "type": "integer",
                                "description": "Required meeting duration in minutes"
                            },
                            "start_time": {
                                "type": "string",
                                "description": "Daily start time (HH:MM format, default: 09:00)",
                                "default": "09:00"
                            },
                            "end_time": {
                                "type": "string",
                                "description": "Daily end time (HH:MM format, default: 18:00)",
                                "default": "18:00"
                            },
                            "exclude_lunch": {
                                "type": "boolean",
                                "description": "Exclude lunch time 12:00-13:00 (default: true)",
                                "default": True
                            }
                        },
                        "required": ["user_id", "start_date", "end_date", "duration_minutes"]
                    }
                ),
                Tool(
                    name="create_meeting",
                    description="Create a meeting with attendees",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "subject": {
                                "type": "string",
                                "description": "Meeting subject/title"
                            },
                            "start_datetime": {
                                "type": "string",
                                "description": "Start datetime (ISO format)"
                            },
                            "end_datetime": {
                                "type": "string",
                                "description": "End datetime (ISO format)"
                            },
                            "attendee_ids": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of attendee user IDs"
                            },
                            "description": {
                                "type": "string",
                                "description": "Meeting description (optional)"
                            }
                        },
                        "required": ["subject", "start_datetime", "end_datetime", "attendee_ids"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            if not self.garoon_client:
                raise Exception("Garoon client not initialized")

            try:
                if name == "get_schedule":
                    result = await self.garoon_client.get_schedule(
                        start_date=arguments["start_date"],
                        end_date=arguments["end_date"],
                        user_id=arguments.get("user_id")
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "create_schedule":
                    schedule_result = await self.garoon_client.create_schedule(
                        subject=arguments["subject"],
                        start_datetime=arguments["start_datetime"],
                        end_datetime=arguments["end_datetime"],
                        description=arguments.get("description")
                    )
                    return [TextContent(type="text", text=f"Schedule created: {schedule_result}")]

                elif name == "search_users":
                    result = await self.garoon_client.search_users(
                        query=arguments["query"],
                        limit=arguments.get("limit", 20)
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "find_available_time":
                    result = await self.garoon_client.find_available_time(
                        user_id=arguments["user_id"],
                        start_date=arguments["start_date"],
                        end_date=arguments["end_date"],
                        duration_minutes=arguments["duration_minutes"],
                        start_time=arguments.get("start_time", "09:00"),
                        end_time=arguments.get("end_time", "18:00"),
                        exclude_lunch=arguments.get("exclude_lunch", True)
                    )
                    return [TextContent(type="text", text=str(result))]

                elif name == "create_meeting":
                    meeting_result = await self.garoon_client.create_meeting(
                        subject=arguments["subject"],
                        start_datetime=arguments["start_datetime"],
                        end_datetime=arguments["end_datetime"],
                        attendee_ids=arguments["attendee_ids"],
                        description=arguments.get("description")
                    )
                    return [TextContent(type="text", text=f"Meeting created: {meeting_result}")]

                else:
                    raise Exception(f"Unknown tool: {name}")

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                raise

async def main() -> None:
    """Main entry point"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Get configuration from environment variables
    base_url = os.getenv("GAROON_BASE_URL")
    g_username = os.getenv("GAROON_USERNAME")
    g_password = os.getenv("GAROON_PASSWORD")

    if not all([base_url, g_username, g_password]):
        logger.error("Missing required environment variables:")
        logger.error("GAROON_BASE_URL, GAROON_USERNAME, GAROON_PASSWORD")
        return

    # Type assertion for mypy - we've already checked these are not None
    assert base_url is not None
    assert g_username is not None
    assert g_password is not None

    # Create and setup server
    mcp_server = GaroonMCPServer()
    mcp_server.setup_handlers()

    # Initialize Garoon client with Garoon credentials
    await mcp_server.initialize(base_url, g_username, g_password)
    
    try:
        # Run server with proper initialization options
        async with stdio_server() as (read_stream, write_stream):
            init_options = mcp_server.server.create_initialization_options()
            await mcp_server.server.run(
                read_stream,
                write_stream,
                init_options
            )
    finally:
        # Ensure Garoon client is properly closed
        if mcp_server.garoon_client:
            await mcp_server.garoon_client.close()

if __name__ == "__main__":
    asyncio.run(main())