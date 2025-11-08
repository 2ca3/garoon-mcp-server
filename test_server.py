#!/usr/bin/env python3.11
"""Quick test for the MCP server"""

import asyncio
import os
import sys
from dotenv import load_dotenv

async def test_server():
    # Set up environment
    load_dotenv()
    
    # Check environment variables
    required_vars = ["GAROON_BASE_URL", "BASIC_USERNAME", "BASIC_PASSWORD", "GAROON_USERNAME", "GAROON_PASSWORD"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {missing}")
        return False
    
    print("✅ Environment variables OK")
    
    # Test imports
    try:
        from main import GaroonMCPServer
        print("✅ Main imports OK")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test server creation
    try:
        server = GaroonMCPServer()
        server.setup_handlers()
        print("✅ Server creation OK")
    except Exception as e:
        print(f"❌ Server creation error: {e}")
        return False
    
    # Test Garoon client initialization
    try:
        base_url = os.getenv("GAROON_BASE_URL")
        b_username = os.getenv("BASIC_USERNAME")
        b_password = os.getenv("BASIC_PASSWORD")
        g_username = os.getenv("GAROON_USERNAME")
        g_password = os.getenv("GAROON_PASSWORD")
        
        await server.initialize(base_url, b_username, b_password, g_username, g_password)
        print("✅ Garoon client initialization OK")
        
        # Clean up
        if server.garoon_client:
            await server.garoon_client.close()
        
        return True
    except Exception as e:
        print(f"❌ Garoon initialization error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)
