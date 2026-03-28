"""FastMCP サーバのユニットテスト"""

from unittest.mock import AsyncMock, patch

import pytest


class TestGetScheduleTool:
    """get_schedule ツールのテスト"""

    @pytest.mark.asyncio
    async def test_get_schedule_returns_string(self):
        """get_schedule がスケジュールを文字列で返すこと"""
        mock_events = [{"id": "1", "subject": "Test Event"}]

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_schedule.return_value = mock_events
            mock_get_client.return_value = mock_client

            from main import get_schedule

            result = await get_schedule(start_date="2025-01-01", end_date="2025-01-31")

            assert isinstance(result, str)
            assert "Test Event" in result
            mock_client.get_schedule.assert_called_once_with(start_date="2025-01-01", end_date="2025-01-31", user_id=None)

    @pytest.mark.asyncio
    async def test_get_schedule_with_user_id(self):
        """user_id を指定してスケジュールを取得できること"""
        mock_events = [{"id": "2", "subject": "Other User Event"}]

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_schedule.return_value = mock_events
            mock_get_client.return_value = mock_client

            from main import get_schedule

            result = await get_schedule(start_date="2025-01-01", end_date="2025-01-31", user_id="123")

            assert "Other User Event" in result
            mock_client.get_schedule.assert_called_once_with(start_date="2025-01-01", end_date="2025-01-31", user_id="123")


class TestCreateScheduleTool:
    """create_schedule ツールのテスト"""

    @pytest.mark.asyncio
    async def test_create_schedule_returns_created_message(self):
        """create_schedule が作成メッセージを返すこと"""
        mock_result = {"id": "new-event-1", "subject": "New Meeting"}

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_schedule.return_value = mock_result
            mock_get_client.return_value = mock_client

            from main import create_schedule

            result = await create_schedule(
                subject="New Meeting",
                start_datetime="2025-01-15T10:00:00+09:00",
                end_datetime="2025-01-15T11:00:00+09:00",
            )

            assert result.startswith("Schedule created:")
            assert "new-event-1" in result

    @pytest.mark.asyncio
    async def test_create_schedule_with_description(self):
        """description を指定してスケジュールを作成できること"""
        mock_result = {"id": "event-2"}

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_schedule.return_value = mock_result
            mock_get_client.return_value = mock_client

            from main import create_schedule

            await create_schedule(
                subject="Meeting with description",
                start_datetime="2025-01-15T10:00:00+09:00",
                end_datetime="2025-01-15T11:00:00+09:00",
                description="This is a description",
            )

            mock_client.create_schedule.assert_called_once_with(
                subject="Meeting with description",
                start_datetime="2025-01-15T10:00:00+09:00",
                end_datetime="2025-01-15T11:00:00+09:00",
                description="This is a description",
                event_menu=None,
            )


class TestSearchUsersTool:
    """search_users ツールのテスト"""

    @pytest.mark.asyncio
    async def test_search_users_returns_string(self):
        """search_users がユーザー一覧を文字列で返すこと"""
        mock_users = [{"id": "1", "name": "Taro Yamada"}]

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_users.return_value = mock_users
            mock_get_client.return_value = mock_client

            from main import search_users

            result = await search_users(query="Yamada")

            assert isinstance(result, str)
            assert "Taro Yamada" in result
            mock_client.search_users.assert_called_once_with(query="Yamada", limit=20)

    @pytest.mark.asyncio
    async def test_search_users_with_custom_limit(self):
        """limit を指定してユーザーを検索できること"""
        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.search_users.return_value = []
            mock_get_client.return_value = mock_client

            from main import search_users

            await search_users(query="test", limit=5)

            mock_client.search_users.assert_called_once_with(query="test", limit=5)


class TestFindAvailableTimeTool:
    """find_available_time ツールのテスト"""

    @pytest.mark.asyncio
    async def test_find_available_time_returns_string(self):
        """find_available_time が空き時間を文字列で返すこと"""
        mock_slots = [{"start": "2025-01-15T09:00:00", "end": "2025-01-15T10:00:00"}]

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.find_available_time.return_value = mock_slots
            mock_get_client.return_value = mock_client

            from main import find_available_time

            result = await find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60,
            )

            assert isinstance(result, str)
            assert "2025-01-15T09:00:00" in result

    @pytest.mark.asyncio
    async def test_find_available_time_passes_all_params(self):
        """全パラメータが正しく渡されること"""
        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.find_available_time.return_value = []
            mock_get_client.return_value = mock_client

            from main import find_available_time

            await find_available_time(
                user_id="456",
                start_date="2025-02-01",
                end_date="2025-02-07",
                duration_minutes=30,
                start_time="10:00",
                end_time="17:00",
                exclude_lunch=False,
            )

            mock_client.find_available_time.assert_called_once_with(
                user_id="456",
                start_date="2025-02-01",
                end_date="2025-02-07",
                duration_minutes=30,
                start_time="10:00",
                end_time="17:00",
                exclude_lunch=False,
            )


class TestCreateMeetingTool:
    """create_meeting ツールのテスト"""

    @pytest.mark.asyncio
    async def test_create_meeting_returns_created_message(self):
        """create_meeting が作成メッセージを返すこと"""
        mock_result = {"id": "meeting-1", "subject": "Team Meeting"}

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_meeting.return_value = mock_result
            mock_get_client.return_value = mock_client

            from main import create_meeting

            result = await create_meeting(
                subject="Team Meeting",
                start_datetime="2025-01-15T14:00:00+09:00",
                end_datetime="2025-01-15T15:00:00+09:00",
                attendee_ids=["1", "2", "3"],
            )

            assert result.startswith("Meeting created:")
            assert "meeting-1" in result

    @pytest.mark.asyncio
    async def test_create_meeting_with_description(self):
        """description を指定してミーティングを作成できること"""
        mock_result = {"id": "meeting-2"}

        with patch("main.get_client", new_callable=AsyncMock) as mock_get_client:
            mock_client = AsyncMock()
            mock_client.create_meeting.return_value = mock_result
            mock_get_client.return_value = mock_client

            from main import create_meeting

            await create_meeting(
                subject="Meeting with agenda",
                start_datetime="2025-01-15T14:00:00+09:00",
                end_datetime="2025-01-15T15:00:00+09:00",
                attendee_ids=["1"],
                description="Agenda: discuss Q1 goals",
            )

            mock_client.create_meeting.assert_called_once_with(
                subject="Meeting with agenda",
                start_datetime="2025-01-15T14:00:00+09:00",
                end_datetime="2025-01-15T15:00:00+09:00",
                attendee_ids=["1"],
                description="Agenda: discuss Q1 goals",
                event_menu=None,
            )


class TestGetClient:
    """get_client のテスト"""

    @pytest.mark.asyncio
    async def test_get_client_raises_when_env_missing(self):
        """環境変数が未設定の場合に RuntimeError が発生すること"""
        import main

        original_client = main._garoon_client
        main._garoon_client = None

        try:
            with (
                patch("main.base_url", ""),
                patch("main.g_username", ""),
                patch("main.g_password", ""),
            ):
                with pytest.raises(RuntimeError, match="Missing required environment variables"):
                    await main.get_client()
        finally:
            main._garoon_client = original_client
