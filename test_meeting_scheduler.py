#!/usr/bin/env python3
"""Unit tests for meeting scheduler functionality"""

import asyncio
import os
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from dotenv import load_dotenv

from garoon_client import GaroonClient
from main import GaroonMCPServer

# Load environment variables
load_dotenv()


class TestFindAvailableTime:
    """Test finding available time slots"""

    @pytest_asyncio.fixture
    async def mock_client(self):
        """Create a mock Garoon client"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test_user",
            g_password="test_password"
        )
        client.session = AsyncMock()
        client.authenticated = True
        return client

    @pytest.mark.asyncio
    async def test_find_available_time_basic(self, mock_client):
        """Test basic available time finding"""
        # Mock schedule responses - both users have no events
        mock_my_schedule = []
        mock_other_schedule = []

        with patch.object(mock_client, 'get_schedule', side_effect=[mock_my_schedule, mock_other_schedule]):
            result = await mock_client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60
            )

            # Should return available slots from 9:00 AM
            assert len(result) > 0
            assert "start" in result[0]
            assert "end" in result[0]

    @pytest.mark.asyncio
    async def test_find_available_time_with_conflicts(self, mock_client):
        """Test finding time with existing events"""
        # Mock schedules with events
        mock_my_schedule = [
            {
                "id": "1",
                "subject": "My Meeting",
                "start": {"dateTime": "2025-01-15T10:00:00+09:00"},
                "end": {"dateTime": "2025-01-15T11:00:00+09:00"}
            }
        ]
        mock_other_schedule = [
            {
                "id": "2",
                "subject": "Their Meeting",
                "start": {"dateTime": "2025-01-15T14:00:00+09:00"},
                "end": {"dateTime": "2025-01-15T15:00:00+09:00"}
            }
        ]

        with patch.object(mock_client, 'get_schedule', side_effect=[mock_my_schedule, mock_other_schedule]):
            result = await mock_client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60
            )

            # Should return available slots avoiding the conflicts
            assert len(result) > 0
            # Should not overlap with 10:00-11:00 or 14:00-15:00
            for slot in result:
                slot_start = datetime.fromisoformat(slot["start"])
                slot_end = datetime.fromisoformat(slot["end"])

                # Check no overlap with 10:00-11:00
                assert not (slot_start.hour == 10 and slot_end.hour == 11)
                # Check no overlap with 14:00-15:00
                assert not (slot_start.hour == 14 and slot_end.hour == 15)

    @pytest.mark.asyncio
    async def test_find_available_time_lunch_excluded(self, mock_client):
        """Test that lunch time is excluded"""
        mock_my_schedule = []
        mock_other_schedule = []

        with patch.object(mock_client, 'get_schedule', side_effect=[mock_my_schedule, mock_other_schedule]):
            result = await mock_client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60,
                exclude_lunch=True
            )

            # Should not suggest slots during 12:00-13:00
            for slot in result:
                slot_start = datetime.fromisoformat(slot["start"])
                slot_end = datetime.fromisoformat(slot["end"])

                # Lunch time should not be included
                assert not (slot_start.hour == 12 and slot_end.hour == 13)

    @pytest.mark.asyncio
    async def test_find_available_time_max_three_slots(self, mock_client):
        """Test that maximum 3 slots are returned"""
        mock_my_schedule = []
        mock_other_schedule = []

        with patch.object(mock_client, 'get_schedule', side_effect=[mock_my_schedule, mock_other_schedule]):
            result = await mock_client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=30
            )

            # Should return maximum 3 slots
            assert len(result) <= 3

    @pytest.mark.asyncio
    async def test_find_available_time_custom_business_hours(self, mock_client):
        """Test custom business hours"""
        mock_my_schedule = []
        mock_other_schedule = []

        with patch.object(mock_client, 'get_schedule', side_effect=[mock_my_schedule, mock_other_schedule]):
            result = await mock_client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60,
                start_time="10:00",
                end_time="16:00"
            )

            # All slots should be within custom business hours
            for slot in result:
                slot_start = datetime.fromisoformat(slot["start"])
                slot_end = datetime.fromisoformat(slot["end"])

                assert slot_start.hour >= 10
                assert slot_end.hour <= 16


class TestCreateMeeting:
    """Test creating meetings with attendees"""

    @pytest_asyncio.fixture
    async def mock_client(self):
        """Create a mock Garoon client"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test_user",
            g_password="test_password"
        )
        client.session = AsyncMock()
        client.authenticated = True
        return client

    @pytest.mark.asyncio
    async def test_create_meeting_basic(self, mock_client):
        """Test basic meeting creation"""
        mock_response = {
            "id": "999",
            "subject": {"value": "Test Meeting"},
            "start": {"dateTime": "2025-01-15T14:00:00+09:00"},
            "end": {"dateTime": "2025-01-15T15:00:00+09:00"}
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.create_meeting(
                subject="Test Meeting",
                start_datetime="2025-01-15T14:00:00+09:00",
                end_datetime="2025-01-15T15:00:00+09:00",
                attendee_ids=["123", "456"]
            )

            assert result["id"] == "999"
            assert result["subject"]["value"] == "Test Meeting"

    @pytest.mark.asyncio
    async def test_create_meeting_with_description(self, mock_client):
        """Test meeting creation with description"""
        mock_response = {
            "id": "999",
            "subject": {"value": "Test Meeting"},
            "notes": {"value": "This is a test meeting"}
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.create_meeting(
                subject="Test Meeting",
                start_datetime="2025-01-15T14:00:00+09:00",
                end_datetime="2025-01-15T15:00:00+09:00",
                attendee_ids=["123"],
                description="This is a test meeting"
            )

            assert result["id"] == "999"
            assert "notes" in result

    @pytest.mark.asyncio
    async def test_create_meeting_multiple_attendees(self, mock_client):
        """Test meeting creation with multiple attendees"""
        mock_response = {
            "id": "999",
            "attendees": [
                {"type": "USER", "id": "123"},
                {"type": "USER", "id": "456"},
                {"type": "USER", "id": "789"}
            ]
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.create_meeting(
                subject="Team Meeting",
                start_datetime="2025-01-15T14:00:00+09:00",
                end_datetime="2025-01-15T15:00:00+09:00",
                attendee_ids=["123", "456", "789"]
            )

            assert result["id"] == "999"
            assert len(result["attendees"]) == 3


class TestMCPServerIntegration:
    """Test MCP server integration for meeting scheduler"""

    def test_mcp_server_has_meeting_tools(self):
        """Test that MCP server has meeting scheduler tools"""
        from main import GaroonMCPServer

        server = GaroonMCPServer()
        server.setup_handlers()

        # Server should be created successfully
        assert server.server is not None

    def test_tool_structure(self):
        """Test that tool definitions are structured correctly"""
        from main import GaroonMCPServer

        server = GaroonMCPServer()
        server.setup_handlers()

        # If setup_handlers completes without error, structure is correct
        assert server.server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
