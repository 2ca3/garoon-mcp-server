#!/usr/bin/env python3
"""Get today's schedule from Garoon"""

import asyncio
import os
from datetime import datetime

from dotenv import load_dotenv

from garoon_client import GaroonClient


async def main():
    load_dotenv()

    base_url = os.getenv("GAROON_BASE_URL")
    username = os.getenv("GAROON_USERNAME")
    password = os.getenv("GAROON_PASSWORD")

    if not all([base_url, username, password]):
        print("環境変数が設定されていません")
        return

    # 今日の日付
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 {today} の予定を取得中...\n")

    # Garoonクライアント初期化
    client = GaroonClient(base_url, username, password)
    await client.authenticate()

    # 今日のスケジュール取得
    events = await client.get_schedule(start_date=today, end_date=today)

    if not events:
        print("今日の予定はありません")
    else:
        print(f"今日の予定: {len(events)}件\n")
        for i, event in enumerate(events, 1):
            subject = event.get("subject", "件名なし")
            event_id = event.get("id", "N/A")

            # 開始・終了時刻
            start = event.get("start", {})
            end = event.get("end", {})
            start_time = start.get("dateTime", "N/A")
            end_time = end.get("dateTime", "N/A")

            print(f"{i}. {subject}")
            print(f"   時間: {start_time} ～ {end_time}")
            print(f"   ID: {event_id}")
            print()

    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
