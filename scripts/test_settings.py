#!/usr/bin/env python3
"""Test settings API."""

import json
import urllib.request

BASE_URL = "http://localhost:3334"


def api_request(method: str, endpoint: str, data: dict | None = None) -> dict:
    """Make an API request."""
    url = f"{BASE_URL}{endpoint}"
    
    headers = {"Content-Type": "application/json"}
    body = None
    if data:
        body = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode("utf-8")}


def main():
    print("=" * 60)
    print("  Settings API Test Suite")
    print("=" * 60)
    print()
    
    # Test 1: Get all settings
    print("[TEST 1] Get all settings")
    result = api_request("GET", "/api/settings")
    print(f"Success: {result.get('success', False)}")
    if result.get("success"):
        print("Settings sections:", list(result.get("data", {}).keys()))
    print()
    
    # Test 2: Get lookup settings
    print("[TEST 2] Get lookup section")
    result = api_request("GET", "/api/settings/lookup")
    print(f"Success: {result.get('success', False)}")
    if result.get("success"):
        data = result.get("data", {})
        print(f"  Strategy: {data.get('strategy')}")
        print(f"  OpenFoodFacts enabled: {data.get('openfoodfacts_enabled')}")
        print(f"  go-upc enabled: {data.get('goupc_enabled')}")
    print()
    
    # Test 3: Update lookup settings
    print("[TEST 3] Update lookup settings (enable go-upc with test key)")
    result = api_request("PUT", "/api/settings/lookup", {
        "values": {
            "goupc_enabled": True,
            "goupc_api_key": "test-api-key-12345"
        }
    })
    print(f"Success: {result.get('success', False)}")
    print(f"Message: {result.get('message', '')}")
    print()
    
    # Test 4: Verify the update
    print("[TEST 4] Verify lookup settings updated")
    result = api_request("GET", "/api/settings/lookup")
    if result.get("success"):
        data = result.get("data", {})
        print(f"  go-upc enabled: {data.get('goupc_enabled')}")
        print(f"  go-upc API key: {data.get('goupc_api_key')}")  # Should be masked
    print()
    
    # Test 5: Update LLM settings
    print("[TEST 5] Update LLM settings (switch to OpenAI preset)")
    result = api_request("PUT", "/api/settings/llm", {
        "values": {
            "provider_preset": "openai",
            "api_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key": "sk-test-key-abc123"
        }
    })
    print(f"Success: {result.get('success', False)}")
    print(f"Message: {result.get('message', '')}")
    print()
    
    # Test 6: Verify LLM update
    print("[TEST 6] Verify LLM settings updated")
    result = api_request("GET", "/api/settings/llm")
    if result.get("success"):
        data = result.get("data", {})
        print(f"  Provider preset: {data.get('provider_preset')}")
        print(f"  API URL: {data.get('api_url')}")
        print(f"  Model: {data.get('model')}")
        print(f"  API Key: {data.get('api_key')}")  # Should be masked
    print()
    
    # Test 7: Check settings file was created
    print("[TEST 7] Check settings file")
    import os
    settings_file = "data/settings.json"
    if os.path.exists(settings_file):
        print(f"  ✓ Settings file created: {settings_file}")
        # Show file size
        size = os.path.getsize(settings_file)
        print(f"  File size: {size} bytes")
    else:
        print(f"  ✗ Settings file not found")
    print()
    
    print("=" * 60)
    print("  Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
