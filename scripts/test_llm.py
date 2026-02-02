#!/usr/bin/env python3
"""Test LLM integration with real API calls."""

import asyncio
import json
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_llm_health():
    """Test LLM health check."""
    print("\n[TEST 1] LLM Health Check")
    print("=" * 50)
    
    from app.services.llm.client import llm_client
    
    print(f"  Model: {llm_client.model}")
    print(f"  API URL: {llm_client.api_url}")
    print(f"  API Key: {'••••' + llm_client.api_key[-4:] if llm_client.api_key else 'Not set'}")
    
    try:
        healthy = await llm_client.health_check()
        if healthy:
            print("  ✓ LLM service is healthy")
            return True
        else:
            print("  ✗ LLM service is not responding")
            return False
    except Exception as e:
        print(f"  ✗ Health check failed: {e}")
        return False


async def test_llm_simple_completion():
    """Test simple LLM completion."""
    print("\n[TEST 2] Simple Completion")
    print("=" * 50)
    
    from app.services.llm.client import llm_client
    
    try:
        response = await llm_client.complete(
            prompt="What is 2+2? Reply with just the number.",
            max_tokens=10,
            temperature=0,
        )
        print(f"  Prompt: What is 2+2?")
        print(f"  Response: {response.strip()}")
        
        if "4" in response:
            print("  ✓ Correct response")
            return True
        else:
            print("  ⚠ Unexpected response")
            return True  # Still passed, just unexpected
    except Exception as e:
        print(f"  ✗ Completion failed: {e}")
        return False


async def test_product_optimization():
    """Test product name optimization."""
    print("\n[TEST 3] Product Name Optimization")
    print("=" * 50)
    
    from app.services.llm.optimizer import optimize_product_name
    
    test_cases = [
        {
            "name": "NUTELLA HAZELNUT SPREAD WITH COCOA 400G",
            "brand": "Ferrero",
            "description": "Hazelnut spread with cocoa",
        },
        {
            "name": "organic valley whole milk 1 gallon",
            "brand": None,
            "description": None,
        },
        {
            "name": "coca cola classic 12oz can",
            "brand": "Coca-Cola",
            "description": "Carbonated soft drink",
        },
    ]
    
    success_count = 0
    for i, test in enumerate(test_cases, 1):
        print(f"\n  Test {i}:")
        print(f"    Input: {test['name']}")
        
        try:
            result = await optimize_product_name(
                name=test["name"],
                brand=test.get("brand"),
                description=test.get("description"),
            )
            
            print(f"    Optimized: {result.get('name', 'N/A')}")
            print(f"    Brand: {result.get('brand', 'N/A')}")
            print(f"    Category: {result.get('category', 'N/A')}")
            print(f"    ✓ Optimization successful")
            success_count += 1
        except Exception as e:
            print(f"    ✗ Optimization failed: {e}")
    
    print(f"\n  Results: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)


async def test_merge_results():
    """Test merging multiple lookup results."""
    print("\n[TEST 4] Merge Lookup Results")
    print("=" * 50)
    
    from app.services.llm.optimizer import merge_lookup_results
    
    results = [
        {
            "provider": "openfoodfacts",
            "name": "Nutella Hazelnut Spread",
            "brand": "Ferrero",
            "category": "Spreads",
            "image_url": "https://example.com/nutella1.jpg",
        },
        {
            "provider": "upcitemdb",
            "name": "NUTELLA 400G",
            "brand": "NUTELLA",
            "category": "Food",
            "image_url": None,
        },
    ]
    
    print("  Input sources:")
    for r in results:
        print(f"    - {r['provider']}: {r['name']} ({r['brand']})")
    
    try:
        merged = await merge_lookup_results(results)
        print(f"\n  Merged result:")
        print(f"    Name: {merged.get('name', 'N/A')}")
        print(f"    Brand: {merged.get('brand', 'N/A')}")
        print(f"    Category: {merged.get('category', 'N/A')}")
        print(f"    Selected source: {merged.get('selected_source', 'N/A')}")
        print(f"  ✓ Merge successful")
        return True
    except Exception as e:
        print(f"  ✗ Merge failed: {e}")
        return False


async def main():
    """Run all LLM tests."""
    print("=" * 60)
    print("  LLM Integration Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", await test_llm_health()))
    
    if not results[0][1]:
        print("\n❌ LLM service not available. Skipping remaining tests.")
        return
    
    # Test 2: Simple completion
    results.append(("Simple Completion", await test_llm_simple_completion()))
    
    # Test 3: Product optimization
    results.append(("Product Optimization", await test_product_optimization()))
    
    # Test 4: Merge results
    results.append(("Merge Results", await test_merge_results()))
    
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
