#!/usr/bin/env python3
"""Test hot-reload of lookup settings."""

import json
import urllib.request

BASE_URL = "http://localhost:3334"


def api_request(method: str, endpoint: str, data: dict | None = None) -> dict:
    """Make an API request."""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": e.code, "detail": e.read().decode("utf-8")}


def scan_barcode(barcode: str, skip_cache: bool = False) -> dict:
    """Scan a barcode."""
    data = {"barcode": barcode}
    if skip_cache:
        data["skip_cache"] = True
    return api_request("POST", "/api/scan", data)


def main():
    print("=" * 60)
    print("  Hot-Reload Test")
    print("=" * 60)
    print()
    
    # Step 1: Get current lookup settings
    print("[STEP 1] Get current settings")
    result = api_request("GET", "/api/settings/lookup")
    if result.get("success"):
        data = result.get("data", {})
        print(f"  OpenFoodFacts enabled: {data.get('openfoodfacts_enabled')}")
        print(f"  go-upc enabled: {data.get('goupc_enabled')}")
        print(f"  UPCitemdb enabled: {data.get('upcitemdb_enabled')}")
        print(f"  Brave enabled: {data.get('brave_enabled')}")
    print()
    
    # Step 2: Scan a barcode with skip_cache to bypass Redis
    print("[STEP 2] Scan barcode with current settings (skip_cache=True)")
    result = scan_barcode("3017620422003", skip_cache=True)  # Nutella
    if result.get("found"):
        print(f"  ✓ Found: {result.get('product', {}).get('name')}")
        print(f"  Provider: {result.get('lookup_provider')}")
    else:
        print(f"  ✗ Not found")
    print()
    
    # Step 3: Disable OpenFoodFacts (should trigger hot-reload)
    print("[STEP 3] Disable OpenFoodFacts via settings")
    result = api_request("PUT", "/api/settings/lookup", {
        "values": {"openfoodfacts_enabled": False}
    })
    print(f"  Save result: {result.get('message', result)}")
    print()
    
    # Step 4: Scan again - should NOT find via OpenFoodFacts (only Brave is enabled but has no key)
    print("[STEP 4] Scan barcode after disabling OpenFoodFacts (skip_cache=True)")
    result = scan_barcode("3017620422003", skip_cache=True)
    if result.get("found"):
        print(f"  Found: {result.get('product', {}).get('name')}")
        print(f"  Provider: {result.get('lookup_provider')}")
    else:
        print(f"  ✓ Not found (as expected - OpenFoodFacts disabled, Brave has no key)")
    print()
    
    # Step 5: Re-enable OpenFoodFacts
    print("[STEP 5] Re-enable OpenFoodFacts")
    result = api_request("PUT", "/api/settings/lookup", {
        "values": {"openfoodfacts_enabled": True}
    })
    print(f"  Save result: {result.get('message', result)}")
    print()
    
    # Step 6: Scan again - should find via OpenFoodFacts
    print("[STEP 6] Scan barcode after re-enabling OpenFoodFacts (skip_cache=True)")
    result = scan_barcode("3017620422003", skip_cache=True)
    if result.get("found"):
        print(f"  ✓ Found: {result.get('product', {}).get('name')}")
        print(f"  Provider: {result.get('lookup_provider')}")
    else:
        print(f"  ✗ Not found (unexpected)")
    print()
    
    print("=" * 60)
    print("  Hot-Reload Test Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
