"""Garoon Client Unit Tests

タイムゾーン機能を含むGaroonクライアントのユニットテスト
"""

import pytest
from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import AsyncMock, MagicMock, patch
from garoon_client import GaroonClient, GaroonAPIError


class TestGaroonClientInitialization:
    """GaroonClient初期化のテスト"""

    def test_timezone_initialization_valid(self):
        """有効なタイムゾーンで初期化できること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )
        assert client.timezone == ZoneInfo("Asia/Tokyo")

    def test_timezone_initialization_utc_default(self):
        """デフォルトでUTCタイムゾーンが設定されること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password"
        )
        assert client.timezone == ZoneInfo("UTC")

    def test_timezone_initialization_invalid(self):
        """無効なタイムゾーンで例外が発生すること"""
        with pytest.raises(Exception):
            GaroonClient(
                base_url="https://test.cybozu.com",
                g_username="test@example.com",
                g_password="password",
                timezone="Invalid/Timezone"
            )

    def test_base_url_trailing_slash_removed(self):
        """ベースURLの末尾スラッシュが削除されること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com/",
            g_username="test@example.com",
            g_password="password"
        )
        assert client.base_url == "https://test.cybozu.com"


@pytest.mark.asyncio
class TestGetScheduleWithTimezone:
    """タイムゾーンを考慮したスケジュール取得のテスト"""

    async def test_get_schedule_with_tokyo_timezone(self):
        """Asia/Tokyoタイムゾーンでスケジュール取得時に正しいISO形式に変換されること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )

        # モックレスポンス
        mock_response = {"events": [{"id": "1", "subject": "Test Event"}]}

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            result = await client.get_schedule("2025-01-01", "2025-01-02")

            # _make_requestが呼ばれたことを確認
            mock_request.assert_called_once()

            # 呼び出し時の引数を確認
            call_args = mock_request.call_args
            params = call_args.kwargs['params']

            # タイムゾーン情報を含むISO形式であることを確認
            assert 'rangeStart' in params
            assert 'rangeEnd' in params
            assert '+09:00' in params['rangeStart']  # JST offset
            assert '+09:00' in params['rangeEnd']

    async def test_get_schedule_with_utc_timezone(self):
        """UTCタイムゾーンでスケジュール取得時に正しいISO形式に変換されること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="UTC"
        )

        mock_response = {"events": []}

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.get_schedule("2025-01-01", "2025-01-02")

            call_args = mock_request.call_args
            params = call_args.kwargs['params']

            # UTC形式であることを確認
            assert '+00:00' in params['rangeStart']
            assert '+00:00' in params['rangeEnd']

    async def test_get_schedule_invalid_date_format(self):
        """無効な日付フォーマットで例外が発生すること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password"
        )

        with pytest.raises(ValueError):
            await client.get_schedule("invalid-date", "2025-01-02")


@pytest.mark.asyncio
class TestFindAvailableTimeWithTimezone:
    """タイムゾーンを考慮した空き時間検索のテスト"""

    async def test_find_available_time_with_timezone(self):
        """タイムゾーンを考慮して空き時間を検索できること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )

        # モック: 空のスケジュール
        mock_my_schedule = []
        mock_other_schedule = []

        with patch.object(client, 'get_schedule', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_my_schedule, mock_other_schedule]

            result = await client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60
            )

            # 空き時間が見つかること
            assert len(result) > 0
            assert 'start' in result[0]
            assert 'end' in result[0]

    async def test_find_available_time_exclude_lunch(self):
        """ランチタイムが除外されること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )

        mock_my_schedule = []
        mock_other_schedule = []

        with patch.object(client, 'get_schedule', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_my_schedule, mock_other_schedule]

            result = await client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60,
                exclude_lunch=True
            )

            # 12:00-13:00の時間帯が避けられていることを確認
            for slot in result:
                start_time = datetime.fromisoformat(slot['start'])
                end_time = datetime.fromisoformat(slot['end'])

                # ランチタイムと重複していないこと
                lunch_start = start_time.replace(hour=12, minute=0)
                lunch_end = start_time.replace(hour=13, minute=0)

                assert not (start_time < lunch_end and end_time > lunch_start)

    async def test_find_available_time_with_busy_schedule(self):
        """予定が入っている場合、その時間を避けて検索できること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )

        # 10:00-11:00に予定があるモック
        mock_schedule = [{
            "start": {"dateTime": "2025-01-15T10:00:00+09:00"},
            "end": {"dateTime": "2025-01-15T11:00:00+09:00"}
        }]

        with patch.object(client, 'get_schedule', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = [mock_schedule, []]

            result = await client.find_available_time(
                user_id="123",
                start_date="2025-01-15",
                end_date="2025-01-15",
                duration_minutes=60,
                start_time="09:00",
                end_time="12:00"
            )

            # 9:00-10:00の空き時間が見つかること
            assert len(result) > 0
            first_slot = result[0]
            start_time = datetime.fromisoformat(first_slot['start'])
            assert start_time.hour == 9


@pytest.mark.asyncio
class TestTimezoneConversionBoundary:
    """タイムゾーン変換の境界ケーステスト"""

    async def test_date_boundary_with_timezone(self):
        """日跨ぎの境界ケースでタイムゾーンが正しく扱われること"""
        client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )

        mock_response = {"events": []}

        with patch.object(client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await client.get_schedule("2025-01-01", "2025-01-01")

            call_args = mock_request.call_args
            params = call_args.kwargs['params']

            # 同じ日でも00:00:00と23:59:59で範囲が設定されること
            start_dt = datetime.fromisoformat(params['rangeStart'])
            end_dt = datetime.fromisoformat(params['rangeEnd'])

            assert start_dt.hour == 0
            assert start_dt.minute == 0
            assert end_dt.hour == 23
            assert end_dt.minute == 59

    async def test_different_timezones_conversion(self):
        """異なるタイムゾーン間で正しく変換されること"""
        tokyo_client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="Asia/Tokyo"
        )

        ny_client = GaroonClient(
            base_url="https://test.cybozu.com",
            g_username="test@example.com",
            g_password="password",
            timezone="America/New_York"
        )

        mock_response = {"events": []}

        with patch.object(tokyo_client, '_make_request', new_callable=AsyncMock) as mock_tokyo:
            mock_tokyo.return_value = mock_response
            await tokyo_client.get_schedule("2025-01-01", "2025-01-01")
            tokyo_params = mock_tokyo.call_args.kwargs['params']

        with patch.object(ny_client, '_make_request', new_callable=AsyncMock) as mock_ny:
            mock_ny.return_value = mock_response
            await ny_client.get_schedule("2025-01-01", "2025-01-01")
            ny_params = mock_ny.call_args.kwargs['params']

        # 異なるタイムゾーンオフセットが設定されていること
        assert tokyo_params['rangeStart'] != ny_params['rangeStart']
        assert '+09:00' in tokyo_params['rangeStart']
        assert '-05:00' in ny_params['rangeStart'] or '-04:00' in ny_params['rangeStart']  # DST考慮
