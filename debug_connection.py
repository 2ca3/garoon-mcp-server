#!/usr/bin/env python3
"""Debug script to test Garoon connection."""

import asyncio
import sys
import aiohttp
import socket


async def test_connection():
    """Test connection to Garoon server."""
    base_url = "https://idyh6.cybozu.com"

    # Test 1: Basic socket connection
    print("Test 1: Basic socket DNS resolution...")
    try:
        result = socket.getaddrinfo("idyh6.cybozu.com", 443, socket.AF_UNSPEC, socket.SOCK_STREAM)
        print(f"✓ Socket DNS resolution successful: {result[0][4]}")
    except Exception as e:
        print(f"✗ Socket DNS resolution failed: {e}")
        return

    # Test 2: aiohttp connection with default resolver
    print("\nTest 2: aiohttp connection (default resolver)...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url}/g/api/v1/base/users", timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"✓ Connection successful: {response.status}")
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")

    # Test 3: aiohttp connection with custom connector (ThreadedResolver)
    print("\nTest 3: aiohttp connection (threaded resolver)...")
    try:
        connector = aiohttp.TCPConnector(use_dns_cache=False, family=socket.AF_INET)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(f"{base_url}/g/api/v1/base/users", timeout=aiohttp.ClientTimeout(total=10)) as response:
                print(f"✓ Connection successful: {response.status}")
    except Exception as e:
        print(f"✗ Connection failed: {type(e).__name__}: {e}")

    # Test 4: Check Python asyncio loop
    print("\nTest 4: Python environment info...")
    print(f"Python version: {sys.version}")
    print(f"Event loop: {type(asyncio.get_event_loop())}")


if __name__ == "__main__":
    asyncio.run(test_connection())
