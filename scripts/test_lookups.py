#!/usr/bin/env python3
"""Test additional barcode lookups."""

import json
import urllib.request

BASE_URL = "http://localhost:3334"

def scan(barcode: str) -> None:
    """Scan a barcode and print result."""
    url = f"{BASE_URL}/api/scan"
    data = json.dumps({"barcode": barcode}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read())
            product = result.get("product")
            if product:
                name = product.get("name", "Unknown")
                brand = product.get("brand", "")
                category = product.get("category", "")
            else:
                name = "Not found"
                brand = ""
                category = ""
            provider = result.get("lookup_provider", "N/A")
            time_ms = result.get("lookup_time_ms", 0)
            found = result.get("found", False)
            
            status = "✅" if found else "❌"
            print(f"{status} {barcode}: {name}")
            if brand:
                print(f"   Brand: {brand}")
            if category:
                print(f"   Category: {category}")
            print(f"   Provider: {provider}, Time: {time_ms}ms")
            print()
    except Exception as e:
        print(f"❌ {barcode}: Error - {e}")
        print()

if __name__ == "__main__":
    print("=" * 60)
    print("  Additional Barcode Lookup Tests")
    print("=" * 60)
    print()
    
    # Various international barcodes
    test_barcodes = [
        ("4006381333931", "German product"),
        ("3017620422003", "Nutella"),
        ("5000159484695", "Heinz"),
        ("8710398507914", "Douwe Egberts Coffee"),
        ("0041270000642", "US product"),
        ("7622210449283", "Oreo cookies"),
    ]
    
    for barcode, description in test_barcodes:
        print(f"Testing: {description}")
        scan(barcode)
