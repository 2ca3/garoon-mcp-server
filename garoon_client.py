"""Garoon API Client

A Python client for interacting with Garoon REST API using X-Cybozu-Authorization header.
"""

import aiohttp
import asyncio
import json
import logging
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

class GaroonAPIError(Exception):
    """Custom exception for Garoon API errors"""
    pass

class GaroonClient:
    """Garoon REST API client using X-Cybozu-Authorization header"""

    def __init__(self, base_url: str, g_username: str, g_password: str, timezone: str = "UTC"):
        """
        Initialize Garoon client

        Args:
            base_url: Garoon base URL (e.g., https://your-garoon.cybozu.com)
            g_username: Garoon API username
            g_password: Garoon API password
            timezone: Timezone name (e.g., 'Asia/Tokyo', 'UTC')

        Raises:
            ValueError: If invalid timezone is provided
        """
        self.base_url = base_url.rstrip('/')
        self.g_username = g_username
        self.g_password = g_password

        try:
            self.timezone = ZoneInfo(timezone)
        except Exception as e:
            raise ValueError(f"Invalid timezone '{timezone}': {e}") from e

        self.session: Optional[aiohttp.ClientSession] = None
        self.authenticated = False

        # Create Garoon token like GAS example: base64Encode(username + ':' + password)
        g_credentials = f"{g_username}:{g_password}"
        self.garoon_token = base64.b64encode(g_credentials.encode('utf-8')).decode('utf-8')

    async def __aenter__(self) -> 'GaroonClient':
        """Async context manager entry"""
        await self.authenticate()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit"""
        await self.close()

    async def authenticate(self) -> None:
        """Authenticate with Garoon using X-Cybozu-Authorization header"""
        if self.session is None:
            # Try different header formats commonly used by Cybozu products
            headers = {
                'X-Cybozu-Authorization': self.garoon_token,
                'Content-Type': 'application/json',
                'User-Agent': 'GaroonMCPServer/1.0'
            }
            self.session = aiohttp.ClientSession(headers=headers)
        
        try:
            # Test with schedule API (commonly available endpoint)
            url = urljoin(self.base_url, "/g/api/v1/schedule/events")
            params: Dict[str, str] = {
                'limit': '1',
                'fields': 'id,subject'
            }
            async with self.session.get(url, params=params) as response:
                response_text = await response.text()
                logger.info(f"Auth test response: {response.status}, content: {response_text[:200]}")
                
                if response.status == 200:
                    self.authenticated = True
                    logger.info("Successfully authenticated with Garoon using X-Cybozu-Authorization header")
                else:
                    raise GaroonAPIError(f"Authentication failed: {response.status} - {response_text}")
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self.close()  # Ensure session is closed on error
            raise GaroonAPIError(f"Authentication failed: {e}")
    

    async def close(self) -> None:
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None
            self.authenticated = False

    async def _make_request(self, method: str, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Make HTTP request to Garoon API"""
        if not self.authenticated:
            await self.authenticate()

        if self.session is None:
            raise GaroonAPIError("Session not initialized")

        url = urljoin(self.base_url, endpoint)

        try:
            async with self.session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    result: Dict[str, Any] = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    raise GaroonAPIError(f"API request failed: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request error: {e}")
            raise GaroonAPIError(f"Request failed: {e}")
    
    async def get_schedule(self, start_date: str, end_date: str, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get schedule events

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            user_id: Optional user ID filter (Garoon user ID)

        Returns:
            List of schedule events

        Raises:
            ValueError: If date format is invalid
        """
        endpoint = "/g/api/v1/schedule/events"

        # Convert date strings to timezone-aware datetime objects
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").replace(
                hour=0, minute=0, second=0, microsecond=0, tzinfo=self.timezone
            )
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=0, tzinfo=self.timezone
            )
        except ValueError as e:
            raise ValueError(f"Invalid date format. Expected YYYY-MM-DD, got start_date='{start_date}', end_date='{end_date}': {e}") from e

        params: Dict[str, str] = {
            "rangeStart": start_dt.isoformat(),
            "rangeEnd": end_dt.isoformat()
        }

        # targetパラメータを指定する場合、targetTypeも必須
        # 参考: https://cybozu.dev/ja/garoon/docs/rest-api/schedule/get-schedule-events/
        if user_id:
            params["target"] = user_id
            params["targetType"] = "user"

        response = await self._make_request("GET", endpoint, params=params)
        events: List[Dict[str, Any]] = response.get("events", [])
        return events
    
    async def create_schedule(self, subject: str, start_datetime: str, end_datetime: str, 
                            description: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new schedule event
        
        Args:
            subject: Event subject/title
            start_datetime: Start datetime in ISO format
            end_datetime: End datetime in ISO format
            description: Optional event description
            
        Returns:
            Created event information
        """
        endpoint = "/g/api/v1/schedule/events"
        
        event_data = {
            "subject": {"value": subject},
            "start": {"dateTime": start_datetime},
            "end": {"dateTime": end_datetime}
        }
        
        if description:
            event_data["notes"] = {"value": description}
            
        response = await self._make_request("POST", endpoint, json=event_data)
        return response
    
    async def get_user_info(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information
        
        Args:
            user_id: Optional user ID (if not provided, returns current user info)
            
        Returns:
            User information
        """
        if user_id:
            endpoint = f"/g/api/v1/users/{user_id}"
        else:
            endpoint = "/g/api/v1/users/me"
            
        response = await self._make_request("GET", endpoint)
        return response
    
    async def get_applications(self) -> List[Dict[str, Any]]:
        """
        Get available applications
        
        Returns:
            List of available applications
        """
        endpoint = "/g/api/v1/base/applications"
        response = await self._make_request("GET", endpoint)
        applications: List[Dict[str, Any]] = response.get("applications", [])
        return applications
    
    async def search_users(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search users

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of matching users
        """
        # Garoon REST APIのユーザー一覧取得エンドポイント
        # 参考: https://cybozu.dev/ja/garoon/docs/rest-api/
        endpoint = "/g/api/v1/base/users"
        params: Dict[str, str] = {
            "name": query,
            "limit": str(limit)
        }

        try:
            response = await self._make_request("GET", endpoint, params=params)
            users: List[Dict[str, Any]] = response.get("users", [])
            return users
        except GaroonAPIError as e:
            # エンドポイントが見つからない場合、空のリストを返す
            if "GRN_REST_API_00101" in str(e):
                logger.warning(f"User search endpoint not available: {e}")
                return []
            raise

    async def find_available_time(
        self,
        user_id: str,
        start_date: str,
        end_date: str,
        duration_minutes: int,
        start_time: str = "09:00",
        end_time: str = "18:00",
        exclude_lunch: bool = True
    ) -> List[Dict[str, str]]:
        """
        Find available time slots for a meeting between the authenticated user and another user

        Args:
            user_id: Other user's Garoon user ID
            start_date: Search start date (YYYY-MM-DD)
            end_date: Search end date (YYYY-MM-DD)
            duration_minutes: Required meeting duration in minutes
            start_time: Daily start time (HH:MM, default: 09:00)
            end_time: Daily end time (HH:MM, default: 18:00)
            exclude_lunch: Exclude lunch time 12:00-13:00 (default: True)

        Returns:
            List of available time slots (max 3), each containing:
            - start: Start datetime (ISO format)
            - end: End datetime (ISO format)
        """
        # Get both users' schedules
        my_schedule = await self.get_schedule(start_date, end_date)
        other_schedule = await self.get_schedule(start_date, end_date, user_id)

        # Merge schedules
        all_events = my_schedule + other_schedule

        # Parse business hours
        start_hour, start_minute = map(int, start_time.split(":"))
        end_hour, end_minute = map(int, end_time.split(":"))

        available_slots: List[Dict[str, str]] = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=self.timezone)
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").replace(tzinfo=self.timezone)

        while current_date <= end_date_obj and len(available_slots) < 3:
            # Set business hours for this day (use naive datetime for comparison)
            day_start = current_date.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0, tzinfo=None)
            day_end = current_date.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0, tzinfo=None)

            # Get events for this day
            day_events = []
            for event in all_events:
                event_start_str = event.get("start", {}).get("dateTime", "")
                event_end_str = event.get("end", {}).get("dateTime", "")

                if not event_start_str or not event_end_str:
                    continue

                # Parse event times (handle various datetime formats)
                try:
                    # Remove timezone info for comparison
                    event_start = datetime.fromisoformat(event_start_str.replace("Z", "+00:00"))
                    event_end = datetime.fromisoformat(event_end_str.replace("Z", "+00:00"))

                    # Convert to naive datetime (remove timezone)
                    event_start = event_start.replace(tzinfo=None)
                    event_end = event_end.replace(tzinfo=None)

                    # Check if event is on this day
                    if event_start.date() == current_date.date() or event_end.date() == current_date.date():
                        day_events.append((event_start, event_end))
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse event datetime: {e}")
                    continue

            # Add lunch time if excluded
            if exclude_lunch:
                # Create naive datetime for consistency with event_start/event_end
                lunch_start = current_date.replace(hour=12, minute=0, second=0, microsecond=0, tzinfo=None)
                lunch_end = current_date.replace(hour=13, minute=0, second=0, microsecond=0, tzinfo=None)
                day_events.append((lunch_start, lunch_end))

            # Sort events by start time
            day_events.sort(key=lambda x: x[0])

            # Find gaps
            current_time = day_start
            for event_start, event_end in day_events:
                # Check if there's a gap before this event
                if event_start > current_time:
                    gap_duration = (event_start - current_time).total_seconds() / 60
                    if gap_duration >= duration_minutes:
                        # Found an available slot
                        slot_end = current_time + timedelta(minutes=duration_minutes)
                        available_slots.append({
                            "start": current_time.isoformat(),
                            "end": slot_end.isoformat()
                        })
                        if len(available_slots) >= 3:
                            break

                # Move current_time forward
                current_time = max(current_time, event_end)

            # Check if there's time left at the end of the day
            if len(available_slots) < 3 and current_time < day_end:
                gap_duration = (day_end - current_time).total_seconds() / 60
                if gap_duration >= duration_minutes:
                    slot_end = current_time + timedelta(minutes=duration_minutes)
                    available_slots.append({
                        "start": current_time.isoformat(),
                        "end": slot_end.isoformat()
                    })

            # Move to next day
            current_date += timedelta(days=1)

        return available_slots

    async def create_meeting(
        self,
        subject: str,
        start_datetime: str,
        end_datetime: str,
        attendee_ids: List[str],
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a meeting with attendees

        Args:
            subject: Meeting subject/title
            start_datetime: Start datetime in ISO format
            end_datetime: End datetime in ISO format
            attendee_ids: List of attendee user IDs
            description: Optional meeting description

        Returns:
            Created meeting information
        """
        endpoint = "/g/api/v1/schedule/events"

        # Build attendees list
        attendees = [{"type": "USER", "id": user_id} for user_id in attendee_ids]

        event_data: Dict[str, Any] = {
            "subject": {"value": subject},
            "start": {"dateTime": start_datetime},
            "end": {"dateTime": end_datetime},
            "attendees": attendees
        }

        if description:
            event_data["notes"] = {"value": description}

        response = await self._make_request("POST", endpoint, json=event_data)
        return response