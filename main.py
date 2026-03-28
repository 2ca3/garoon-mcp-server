#!/usr/bin/env python3
"""Garoon MCP Server

A Model Context Protocol (MCP) server for Garoon API integration.
Uses X-Cybozu-Authorization header with Base64 encoded credentials.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from garoon_client import GaroonClient

# Configure logging to use stderr to avoid interfering with MCP JSON-RPC on stdout
logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(name)s: %(message)s")
logger = logging.getLogger(__name__)

garoon_logger = logging.getLogger("garoon_client")
garoon_logger.setLevel(logging.INFO)

# Load environment variables from .env file
load_dotenv()

base_url = os.getenv("GAROON_BASE_URL", "")
g_username = os.getenv("GAROON_USERNAME", "")
g_password = os.getenv("GAROON_PASSWORD", "")
timezone = os.getenv("GAROON_TIMEZONE", "UTC")

mcp = FastMCP("garoon-mcp")
_garoon_client: GaroonClient | None = None


async def get_client() -> GaroonClient:
    """Get or initialize the Garoon client."""
    global _garoon_client
    if _garoon_client is None:
        if not all([base_url, g_username, g_password]):
            raise RuntimeError("Missing required environment variables: GAROON_BASE_URL, GAROON_USERNAME, GAROON_PASSWORD")
        _garoon_client = GaroonClient(base_url, g_username, g_password, timezone)
        await _garoon_client.authenticate()
        logger.info(f"Garoon client initialized successfully (timezone: {timezone})")
    return _garoon_client


@mcp.tool()
async def get_schedule(start_date: str, end_date: str, user_id: str | None = None) -> str:
    """Get schedule events from Garoon for yourself or other users.

    Parameters
    ----------
    start_date : str
        Start date (YYYY-MM-DD format).
    end_date : str
        End date (YYYY-MM-DD format).
    user_id : str, optional
        User ID to get schedule for. If not specified, returns your own schedule.
        Use search_users tool to find user IDs.
    """
    client = await get_client()
    result = await client.get_schedule(start_date=start_date, end_date=end_date, user_id=user_id)
    return str(result)


@mcp.tool()
async def create_schedule(
    subject: str,
    start_datetime: str,
    end_datetime: str,
    description: str | None = None,
    event_menu: str | None = None,
) -> str:
    """Create a new schedule event in Garoon.

    Parameters
    ----------
    subject : str
        Event subject/title.
    start_datetime : str
        Start datetime (ISO format).
    end_datetime : str
        End datetime (ISO format).
    description : str, optional
        Event description.
    event_menu : str, optional
        Event menu/category (e.g. "会議", "外出"). Defaults to "-----" if omitted.
    """
    client = await get_client()
    result = await client.create_schedule(
        subject=subject,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        description=description,
        event_menu=event_menu,
    )
    return f"Schedule created: {result}"


@mcp.tool()
async def search_users(query: str, limit: int = 20) -> str:
    """Search for users in Garoon by name or other criteria.

    Parameters
    ----------
    query : str
        Search query (user name, email, etc.).
    limit : int, optional
        Maximum number of results to return (default: 20).
    """
    client = await get_client()
    result = await client.search_users(query=query, limit=limit)
    return str(result)


@mcp.tool()
async def find_available_time(
    user_id: str,
    start_date: str,
    end_date: str,
    duration_minutes: int,
    start_time: str = "09:00",
    end_time: str = "18:00",
    exclude_lunch: bool = True,
) -> str:
    """Find available time slots for a meeting with another user.

    Parameters
    ----------
    user_id : str
        Other user's Garoon user ID.
    start_date : str
        Search start date (YYYY-MM-DD format).
    end_date : str
        Search end date (YYYY-MM-DD format).
    duration_minutes : int
        Required meeting duration in minutes.
    start_time : str, optional
        Daily start time (HH:MM format, default: 09:00).
    end_time : str, optional
        Daily end time (HH:MM format, default: 18:00).
    exclude_lunch : bool, optional
        Exclude lunch time 12:00-13:00 (default: True).
    """
    client = await get_client()
    result = await client.find_available_time(
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        duration_minutes=duration_minutes,
        start_time=start_time,
        end_time=end_time,
        exclude_lunch=exclude_lunch,
    )
    return str(result)


@mcp.tool()
async def create_meeting(
    subject: str,
    start_datetime: str,
    end_datetime: str,
    attendee_ids: list[str],
    description: str | None = None,
    event_menu: str | None = None,
) -> str:
    """Create a meeting with attendees.

    Parameters
    ----------
    subject : str
        Meeting subject/title.
    start_datetime : str
        Start datetime (ISO format).
    end_datetime : str
        End datetime (ISO format).
    attendee_ids : list[str]
        List of attendee user IDs.
    description : str, optional
        Meeting description.
    event_menu : str, optional
        Event menu/category (e.g. "会議", "外出"). Defaults to "-----" if omitted.
    """
    client = await get_client()
    result = await client.create_meeting(
        subject=subject,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        attendee_ids=attendee_ids,
        description=description,
        event_menu=event_menu,
    )
    return f"Meeting created: {result}"


if __name__ == "__main__":
    mcp.run()
