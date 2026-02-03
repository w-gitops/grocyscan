#!/usr/bin/env python3
"""Test the LLM models API endpoint."""

import json
import urllib.request


def test_models_endpoint():
    """Test the models endpoint."""
    print("\n[TEST] LLM Models Endpoint")
    print("=" * 50)
    
    url = "http://localhost:3334/api/settings/llm/models"
    
    try:
        with urllib.request.urlopen(url, timeout=20) as response:
            result = json.loads(response.read().decode())
        
        if result.get("success"):
            models = result.get("models", [])
            provider = result.get("provider", "unknown")
            
            print(f"  Provider: {provider}")
            print(f"  Total models: {len(models)}")
            
            if models:
                print("\n  Top 10 models:")
                for i, model in enumerate(models[:10], 1):
                    print(f"    {i}. {model}")
                
                if len(models) > 10:
                    print(f"    ... and {len(models) - 10} more")
            
            print("\n  ✓ Models endpoint working")
            return True
        else:
            print(f"  ✗ Endpoint returned error: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"  ✗ Request failed: {e}")
        return False


def test_model_selection():
    """Test selecting a model via settings API."""
    print("\n[TEST] Model Selection via Settings")
    print("=" * 50)
    
    # First get current settings
    get_url = "http://localhost:3334/api/settings/llm"
    try:
        with urllib.request.urlopen(get_url, timeout=10) as response:
            result = json.loads(response.read().decode())
        
        current_model = result.get("data", {}).get("model")
        print(f"  Current model: {current_model}")
        
        # Update to a different model
        new_model = "gpt-4o"
        if current_model == new_model:
            new_model = "gpt-4o-mini"
        
        put_url = "http://localhost:3334/api/settings/llm"
        data = json.dumps({"values": {"model": new_model}}).encode()
        req = urllib.request.Request(put_url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode())
        
        if result.get("success"):
            print(f"  Updated model to: {new_model}")
            print("  ✓ Model selection working")
            
            # Restore original model
            data = json.dumps({"values": {"model": current_model}}).encode()
            req = urllib.request.Request(put_url, data=data, headers={"Content-Type": "application/json"}, method="PUT")
            with urllib.request.urlopen(req, timeout=10) as response:
                pass
            print(f"  Restored to: {current_model}")
            
            return True
        else:
            print(f"  ✗ Update failed: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"  ✗ Request failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("  LLM Models API Test Suite")
    print("=" * 60)
    
    results = []
    
    results.append(("Models Endpoint", test_models_endpoint()))
    results.append(("Model Selection", test_model_selection()))
    
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
    main()
