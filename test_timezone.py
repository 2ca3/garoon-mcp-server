#!/usr/bin/env python3
"""Unit tests for timezone functionality in GaroonClient"""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import Mock, AsyncMock, patch
from garoon_client import GaroonClient


class TestTimezone(unittest.TestCase):
    """Test timezone handling in GaroonClient"""

    def test_client_initialization_with_timezone(self):
        """Test that GaroonClient initializes with a specified timezone"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test",
            g_password="test",
            timezone="Asia/Tokyo"
        )
        self.assertEqual(client.timezone, ZoneInfo("Asia/Tokyo"))

    def test_client_initialization_default_timezone(self):
        """Test that GaroonClient defaults to UTC if no timezone is specified"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test",
            g_password="test"
        )
        self.assertEqual(client.timezone, ZoneInfo("UTC"))

    @patch('garoon_client.GaroonClient._make_request')
    async def test_get_schedule_with_tokyo_timezone(self, mock_request):
        """Test that get_schedule uses the correct timezone for date conversion"""
        # Setup mock
        mock_request.return_value = {"events": []}

        # Create client with Tokyo timezone
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test",
            g_password="test",
            timezone="Asia/Tokyo"
        )
        client.authenticated = True
        client.session = Mock()

        # Call get_schedule
        await client.get_schedule("2025-11-29", "2025-11-29")

        # Verify the request was made with Tokyo timezone
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        params = call_args[1]['params']

        # Check that the timezone offset is correct for Tokyo (UTC+9)
        self.assertIn("+09:00", params['rangeStart'])
        self.assertIn("+09:00", params['rangeEnd'])

    @patch('garoon_client.GaroonClient._make_request')
    async def test_get_schedule_with_utc_timezone(self, mock_request):
        """Test that get_schedule uses UTC correctly"""
        # Setup mock
        mock_request.return_value = {"events": []}

        # Create client with UTC timezone
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test",
            g_password="test",
            timezone="UTC"
        )
        client.authenticated = True
        client.session = Mock()

        # Call get_schedule
        await client.get_schedule("2025-11-29", "2025-11-29")

        # Verify the request was made with UTC timezone
        mock_request.assert_called_once()
        call_args = mock_request.call_args
        params = call_args[1]['params']

        # Check that the timezone offset is correct for UTC
        self.assertIn("+00:00", params['rangeStart'])
        self.assertIn("+00:00", params['rangeEnd'])

    def test_timezone_aware_datetime_parsing(self):
        """Test that dates are correctly parsed with timezone information"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test",
            g_password="test",
            timezone="Asia/Tokyo"
        )

        # Parse a date string with Tokyo timezone
        test_date = datetime.strptime("2025-11-29", "%Y-%m-%d").replace(
            hour=0, minute=0, second=0, microsecond=0, tzinfo=client.timezone
        )

        # Verify the datetime has timezone information
        self.assertIsNotNone(test_date.tzinfo)
        self.assertEqual(test_date.tzinfo, ZoneInfo("Asia/Tokyo"))

        # Verify the time is midnight in Tokyo
        self.assertEqual(test_date.hour, 0)
        self.assertEqual(test_date.minute, 0)


class TestTimezoneIntegration(unittest.IsolatedAsyncioTestCase):
    """Integration tests for timezone functionality"""

    async def test_full_schedule_flow_with_timezone(self):
        """Test the complete schedule retrieval flow with timezone"""
        with patch('garoon_client.GaroonClient._make_request') as mock_request:
            # Setup mock
            mock_request.return_value = {"events": [
                {
                    "id": "1",
                    "subject": {"value": "Test Event"},
                    "start": {"dateTime": "2025-11-29T09:00:00+09:00"},
                    "end": {"dateTime": "2025-11-29T10:00:00+09:00"}
                }
            ]}

            # Create client with Tokyo timezone
            client = GaroonClient(
                base_url="https://test.cybozu.com",
                g_username="test",
                g_password="test",
                timezone="Asia/Tokyo"
            )
            client.authenticated = True
            client.session = Mock()

            # Get schedule
            events = await client.get_schedule("2025-11-29", "2025-11-29")

            # Verify results
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0]["subject"]["value"], "Test Event")

            # Verify the request used Tokyo timezone
            call_args = mock_request.call_args
            params = call_args[1]['params']
            self.assertIn("+09:00", params['rangeStart'])


if __name__ == '__main__':
    unittest.main()
