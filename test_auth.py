#!/usr/bin/env python3
"""Test script for Garoon authentication with X-Cybozu-Authorization header"""

import asyncio
import base64
import os
from dotenv import load_dotenv
from garoon_client import GaroonClient

async def test_garoon_auth():
    """Test Garoon authentication with X-Cybozu-Authorization header"""
    load_dotenv()

    base_url = os.getenv("GAROON_BASE_URL")
    garoon_username = os.getenv("GAROON_USERNAME")
    garoon_password = os.getenv("GAROON_PASSWORD")

    if not all([base_url, garoon_username, garoon_password]):
        print("❌ Missing required environment variables:")
        print(f"   GAROON_BASE_URL: {base_url}")
        print(f"   GAROON_USERNAME: {garoon_username}")
        print(f"   GAROON_PASSWORD: {'*' * len(garoon_password) if garoon_password else None}")
        return

    print(f"Testing Garoon authentication...")
    print(f"Base URL: {base_url}")
    print(f"Garoon User: {garoon_username}")

    # Create Garoon token
    garoon_credentials = f"{garoon_username}:{garoon_password}"
    garoon_token = base64.b64encode(garoon_credentials.encode('utf-8')).decode('utf-8')

    print(f"Garoon token: {garoon_token}")

    try:
        # Test with Garoon credentials
        print("\n--- Testing with X-Cybozu-Authorization ---")
        client = GaroonClient(base_url, garoon_username, garoon_password)
        await client.authenticate()
        print("✅ Authentication successful!")

        # Test a simple API call
        try:
            apps = await client._make_request("GET", "/g/api/v1/schedule/events", params={'limit': 1, 'fields': 'id,subject'})
            print(f"✅ API call successful, response: {str(apps)[:100]}...")
        except Exception as api_error:
            print(f"⚠️ API call failed: {api_error}")

        await client.close()

    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        if 'client' in locals():
            await client.close()

if __name__ == "__main__":
    asyncio.run(test_garoon_auth())
