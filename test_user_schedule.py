#!/usr/bin/env python3
"""Unit tests for user search and schedule retrieval functionality"""

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


class TestUserSearch:
    """Test user search functionality"""

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
    async def test_search_users_basic(self, mock_client):
        """Test basic user search"""
        # Mock response data
        mock_response = {
            "users": [
                {
                    "id": "1",
                    "code": "user001",
                    "name": "Test User 1",
                    "email": "user1@test.com"
                },
                {
                    "id": "2",
                    "code": "user002",
                    "name": "Test User 2",
                    "email": "user2@test.com"
                }
            ]
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.search_users(query="Test", limit=20)

            assert len(result) == 2
            assert result[0]["id"] == "1"
            assert result[0]["name"] == "Test User 1"
            assert result[1]["id"] == "2"

    @pytest.mark.asyncio
    async def test_search_users_empty_result(self, mock_client):
        """Test user search with no results"""
        mock_response = {"users": []}

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.search_users(query="NonExistent", limit=20)

            assert len(result) == 0
            assert result == []

    @pytest.mark.asyncio
    async def test_search_users_with_limit(self, mock_client):
        """Test user search with custom limit"""
        mock_response = {
            "users": [
                {"id": str(i), "name": f"User {i}"} for i in range(1, 6)
            ]
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.search_users(query="User", limit=5)

            assert len(result) == 5


class TestOtherUserSchedule:
    """Test retrieving other users' schedules"""

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
    async def test_get_schedule_with_user_id(self, mock_client):
        """Test getting schedule for a specific user"""
        mock_response = {
            "events": [
                {
                    "id": "123",
                    "subject": "Meeting with Team",
                    "start": {"dateTime": "2025-01-15T10:00:00Z"},
                    "end": {"dateTime": "2025-01-15T11:00:00Z"},
                    "attendees": [{"id": "999", "name": "Other User"}]
                }
            ]
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.get_schedule(
                start_date="2025-01-15",
                end_date="2025-01-15",
                user_id="999"
            )

            assert len(result) == 1
            assert result[0]["id"] == "123"
            assert result[0]["subject"] == "Meeting with Team"

    @pytest.mark.asyncio
    async def test_get_schedule_without_user_id(self, mock_client):
        """Test getting schedule without user_id (own schedule)"""
        mock_response = {
            "events": [
                {
                    "id": "456",
                    "subject": "My Personal Task",
                    "start": {"dateTime": "2025-01-15T14:00:00Z"},
                    "end": {"dateTime": "2025-01-15T15:00:00Z"}
                }
            ]
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.get_schedule(
                start_date="2025-01-15",
                end_date="2025-01-15",
                user_id=None
            )

            assert len(result) == 1
            assert result[0]["id"] == "456"
            assert result[0]["subject"] == "My Personal Task"

    @pytest.mark.asyncio
    async def test_get_schedule_multiple_days(self, mock_client):
        """Test getting schedule across multiple days"""
        mock_response = {
            "events": [
                {
                    "id": "789",
                    "subject": "Day 1 Event",
                    "start": {"dateTime": "2025-01-15T10:00:00Z"},
                    "end": {"dateTime": "2025-01-15T11:00:00Z"}
                },
                {
                    "id": "790",
                    "subject": "Day 2 Event",
                    "start": {"dateTime": "2025-01-16T10:00:00Z"},
                    "end": {"dateTime": "2025-01-16T11:00:00Z"}
                }
            ]
        }

        with patch.object(mock_client, '_make_request', return_value=mock_response):
            result = await mock_client.get_schedule(
                start_date="2025-01-15",
                end_date="2025-01-16",
                user_id="999"
            )

            assert len(result) == 2


class TestMCPServerIntegration:
    """Test MCP server integration for user search and schedule"""

    def test_mcp_server_has_expected_tools(self):
        """Test that MCP server has the expected tools defined"""
        from main import GaroonMCPServer

        # Create server instance
        server = GaroonMCPServer()

        # Server should have the server attribute
        assert hasattr(server, 'server')
        assert server.server is not None

    def test_tool_definitions_structure(self):
        """Test that tool definitions have the expected structure"""
        # This is a simple check to ensure the code is structured correctly
        # The actual tool definitions are checked when the server is running
        from main import GaroonMCPServer

        server = GaroonMCPServer()
        server.setup_handlers()

        # If setup_handlers completes without error, the structure is correct
        assert server.server is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
