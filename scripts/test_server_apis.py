#!/usr/bin/env python3
"""Quick test of new APIs on the server (run on server via ssh)."""
import json
import urllib.request

BASE = "http://localhost:3334"

def post(path, data):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(data).encode(),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())

def main():
    print("1. POST /api/products/search ...")
    r = post("/api/products/search", {"query": "milk", "limit": 3})
    print(f"   Results: {len(r.get('results', []))} items, query={r.get('query')}")
    print()

    print("2. POST /api/scan/by-product ...")
    r = post("/api/scan/by-product", {"name": "Test Product", "category": "Test"})
    print(f"   scan_id={r.get('scan_id')}, name={r.get('name')}")
    print()

    print("OK")

if __name__ == "__main__":
    main()
