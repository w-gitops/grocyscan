#!/usr/bin/env python3
"""Test Brave Search integration with real API calls."""

import asyncio
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_brave_settings():
    """Check Brave Search settings."""
    print("\n[TEST 1] Brave Search Settings")
    print("=" * 50)
    
    from app.services.lookup.brave import BraveSearchProvider
    
    provider = BraveSearchProvider()
    
    enabled = provider.is_enabled()
    api_key = provider.get_api_key()
    
    print(f"  Enabled: {enabled}")
    print(f"  API Key: {'••••' + api_key[-4:] if api_key else 'Not set'}")
    print(f"  Use as fallback: {provider.use_as_fallback}")
    print(f"  Timeout: {provider.timeout}s")
    
    if enabled and api_key:
        print("  ✓ Brave Search is configured")
        return True
    else:
        if not enabled:
            print("  ⚠ Brave Search is disabled in settings")
        if not api_key:
            print("  ⚠ Brave Search API key not set")
        return False


async def test_brave_health():
    """Test Brave Search API health."""
    print("\n[TEST 2] Brave Search API Health")
    print("=" * 50)
    
    from app.services.lookup.brave import BraveSearchProvider
    
    provider = BraveSearchProvider()
    
    try:
        healthy = await provider.health_check()
        if healthy:
            print("  ✓ Brave Search API is responding")
            return True
        else:
            print("  ✗ Brave Search API check failed (might be disabled or no key)")
            return False
    except Exception as e:
        print(f"  ✗ Health check error: {e}")
        return False


async def test_brave_lookup():
    """Test Brave Search barcode lookups."""
    print("\n[TEST 3] Brave Search Barcode Lookups")
    print("=" * 50)
    
    from app.services.lookup.brave import BraveSearchProvider
    
    provider = BraveSearchProvider()
    
    if not provider.is_enabled() or not provider.get_api_key():
        print("  ⚠ Skipping - Brave Search not configured")
        return None
    
    # Test barcodes that might not be in other databases
    test_barcodes = [
        ("3017620422003", "Nutella (common product)"),
        ("4006381333931", "German product"),
        ("8710398507914", "Douwe Egberts Coffee"),
    ]
    
    success_count = 0
    for barcode, description in test_barcodes:
        print(f"\n  Testing: {description}")
        print(f"    Barcode: {barcode}")
        
        try:
            result = await provider.lookup(barcode)
            
            if result.found:
                print(f"    ✓ Found: {result.name}")
                if result.description:
                    print(f"      Description: {result.description[:80]}...")
                print(f"      Lookup time: {result.lookup_time_ms}ms")
                success_count += 1
            else:
                print(f"    ✗ Not found (lookup time: {result.lookup_time_ms}ms)")
        except Exception as e:
            print(f"    ✗ Lookup error: {e}")
    
    print(f"\n  Results: {success_count}/{len(test_barcodes)} products found")
    return success_count > 0


async def test_brave_via_scan_api():
    """Test Brave Search via the scan API endpoint."""
    print("\n[TEST 4] Brave Search via Scan API")
    print("=" * 50)
    
    import json
    import urllib.request
    
    # First disable OpenFoodFacts to force Brave Search usage
    print("  Temporarily disabling OpenFoodFacts to test Brave fallback...")
    
    # Save lookup settings
    save_url = "http://localhost:3334/api/settings/lookup"
    
    # Disable OpenFoodFacts
    try:
        data = json.dumps({"values": {"openfoodfacts_enabled": False}}).encode()
        req = urllib.request.Request(save_url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
        print("  OpenFoodFacts disabled")
    except Exception as e:
        print(f"  ⚠ Could not disable OpenFoodFacts: {e}")
    
    # Test scan
    scan_url = "http://localhost:3334/api/scan"
    test_barcode = "3017620422003"
    
    try:
        data = json.dumps({"barcode": test_barcode, "skip_cache": True}).encode()
        req = urllib.request.Request(scan_url, data=data, headers={"Content-Type": "application/json"})
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
        
        if result.get("found"):
            print(f"\n  ✓ Scan successful")
            print(f"    Product: {result.get('product', {}).get('name', 'N/A')}")
            print(f"    Provider: {result.get('lookup_provider', 'N/A')}")
            print(f"    Lookup time: {result.get('lookup_time_ms', 0)}ms")
            success = True
        else:
            print(f"\n  ✗ Product not found")
            success = False
    except Exception as e:
        print(f"\n  ✗ Scan failed: {e}")
        success = False
    
    # Re-enable OpenFoodFacts
    try:
        data = json.dumps({"values": {"openfoodfacts_enabled": True}}).encode()
        req = urllib.request.Request(save_url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
        with urllib.request.urlopen(req, timeout=10) as resp:
            pass
        print("\n  OpenFoodFacts re-enabled")
    except Exception as e:
        print(f"\n  ⚠ Could not re-enable OpenFoodFacts: {e}")
    
    return success


async def main():
    """Run all Brave Search tests."""
    print("=" * 60)
    print("  Brave Search Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Settings check
    results.append(("Settings Check", await test_brave_settings()))
    
    if not results[0][1]:
        print("\n⚠ Brave Search not fully configured. Some tests may be skipped.")
    
    # Test 2: Health check
    results.append(("API Health", await test_brave_health()))
    
    # Test 3: Direct lookups
    lookup_result = await test_brave_lookup()
    if lookup_result is not None:
        results.append(("Direct Lookups", lookup_result))
    
    # Test 4: Via Scan API
    results.append(("Scan API Integration", await test_brave_via_scan_api()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
