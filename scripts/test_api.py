#!/usr/bin/env python3
"""GrocyScan API Test Suite."""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

BASE_URL = "http://localhost:3334"


def api_request(
    method: str,
    endpoint: str,
    data: dict | None = None,
    cookies: dict | None = None,
) -> tuple[int, Any, dict]:
    """Make an API request.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        data: JSON body data
        cookies: Cookies to send
        
    Returns:
        Tuple of (status_code, response_data, response_headers)
    """
    url = f"{BASE_URL}{endpoint}"
    
    headers = {"Content-Type": "application/json"}
    if cookies:
        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
        headers["Cookie"] = cookie_str
    
    body = None
    if data:
        body = json.dumps(data).encode("utf-8")
    
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_data = json.loads(response.read().decode("utf-8"))
            # Extract Set-Cookie header
            resp_cookies = {}
            for cookie_header in response.headers.get_all("Set-Cookie") or []:
                parts = cookie_header.split(";")[0]
                if "=" in parts:
                    k, v = parts.split("=", 1)
                    resp_cookies[k.strip()] = v.strip()
            return response.status, resp_data, resp_cookies
    except urllib.error.HTTPError as e:
        resp_data = json.loads(e.read().decode("utf-8"))
        return e.code, resp_data, {}
    except urllib.error.URLError as e:
        return 0, {"error": str(e)}, {}


def test_health():
    """Test health endpoint."""
    print("\n[TEST 1] Health Endpoint")
    print("=" * 40)
    status, data, _ = api_request("GET", "/api/health")
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if status == 200 and data.get("status") == "healthy":
        print("✅ PASS: Health endpoint working")
        return True
    print("❌ FAIL: Health endpoint not working")
    return False


def test_login():
    """Test login endpoint."""
    print("\n[TEST 2] Login Endpoint")
    print("=" * 40)
    status, data, cookies = api_request(
        "POST",
        "/api/auth/login",
        {"username": "admin", "password": "admin"},
    )
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if status == 200 and data.get("success"):
        print("✅ PASS: Login successful")
        return cookies
    print("⚠️ WARNING: Login returned non-200 (auth may be disabled)")
    return cookies


def test_scan(cookies: dict):
    """Test scan endpoint with various barcodes."""
    print("\n[TEST 3] Scan Endpoint - EAN-13")
    print("=" * 40)
    
    # Test valid EAN-13
    status, data, _ = api_request(
        "POST",
        "/api/scan",
        {"barcode": "5901234123457"},
        cookies,
    )
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if status == 200:
        print("✅ PASS: Scan endpoint working")
    else:
        print("❌ FAIL: Scan endpoint returned error")
    
    # Test UPC-A
    print("\n[TEST 4] Scan Endpoint - UPC-A")
    print("=" * 40)
    status, data, _ = api_request(
        "POST",
        "/api/scan",
        {"barcode": "012345678905"},
        cookies,
    )
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test Location barcode
    print("\n[TEST 5] Scan Endpoint - Location")
    print("=" * 40)
    status, data, _ = api_request(
        "POST",
        "/api/scan",
        {"barcode": "LOC-A-001"},
        cookies,
    )
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    # Test invalid barcode
    print("\n[TEST 6] Scan Endpoint - Invalid")
    print("=" * 40)
    status, data, _ = api_request(
        "POST",
        "/api/scan",
        {"barcode": "invalid"},
        cookies,
    )
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")


def test_products(cookies: dict):
    """Test products endpoint."""
    print("\n[TEST 7] Products Endpoint")
    print("=" * 40)
    status, data, _ = api_request("GET", "/api/products", cookies=cookies)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")


def test_locations(cookies: dict):
    """Test locations endpoint."""
    print("\n[TEST 8] Locations Endpoint")
    print("=" * 40)
    status, data, _ = api_request("GET", "/api/locations", cookies=cookies)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")


def test_jobs(cookies: dict):
    """Test jobs endpoint."""
    print("\n[TEST 9] Jobs Endpoint")
    print("=" * 40)
    status, data, _ = api_request("GET", "/api/jobs", cookies=cookies)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if status == 200:
        print("✅ PASS: Jobs endpoint working")
    else:
        print("❌ FAIL: Jobs endpoint returned error")


def test_settings(cookies: dict):
    """Test settings endpoint."""
    print("\n[TEST 10] Settings Endpoint")
    print("=" * 40)
    status, data, _ = api_request("GET", "/api/settings", cookies=cookies)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")


def test_logout(cookies: dict):
    """Test logout endpoint."""
    print("\n[TEST 11] Logout Endpoint")
    print("=" * 40)
    status, data, _ = api_request("POST", "/api/auth/logout", cookies=cookies)
    print(f"Status: {status}")
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if status == 200 and data.get("success"):
        print("✅ PASS: Logout successful")
    else:
        print("⚠️ WARNING: Logout returned non-200")


def main():
    """Run all tests."""
    print("=" * 50)
    print("  GrocyScan API Test Suite")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("\n❌ Server not healthy, aborting tests")
        sys.exit(1)
    
    # Test login
    cookies = test_login()
    
    # Test scan
    test_scan(cookies)
    
    # Test other endpoints
    test_products(cookies)
    test_locations(cookies)
    test_jobs(cookies)
    test_settings(cookies)
    
    # Test logout
    test_logout(cookies)
    
    print("\n" + "=" * 50)
    print("  Test Suite Complete")
    print("=" * 50)


if __name__ == "__main__":
    main()
