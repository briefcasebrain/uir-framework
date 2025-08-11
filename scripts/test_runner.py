#!/usr/bin/env python3
"""
Test runner to demonstrate which tests pass/fail
"""

import subprocess
import sys

def run_test_category(category, description):
    """Run a category of tests and report results"""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    
    cmd = ["python3", "-m", "pytest", category, "-q", "--tb=no", "--no-header"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Parse output
    output = result.stdout
    if "passed" in output or "failed" in output:
        print(output.split('\n')[-2])  # Print summary line
    else:
        print("Could not run tests - missing dependencies")
    
    return result.returncode == 0

def main():
    """Run different test categories and summarize results"""
    
    print("UIR Framework Test Analysis")
    print("Note: Many tests will fail due to missing dependencies and stubbed functionality")
    
    test_categories = [
        ("tests/test_core/test_circuit_breaker.py", "Circuit Breaker (Should Pass)"),
        ("tests/test_core/test_rate_limiter.py", "Rate Limiter (Should Pass)"),
        ("tests/test_providers", "Provider Adapters (Will Fail - Missing Configs)"),
        ("tests/test_router.py", "Router Service (Will Fail - Import Issues)"),
        ("tests/test_query_processor.py", "Query Processor (Partial Pass)"),
        ("tests/test_aggregator.py", "Aggregator (Should Pass)"),
        ("tests/test_cache.py", "Cache Layer (Partial Pass)"),
        ("tests/test_auth.py", "Authentication (Should Pass)"),
        ("tests/test_client.py", "Client SDK (Should Pass with Mocks)"),
    ]
    
    results = {}
    for test_path, description in test_categories:
        try:
            results[description] = run_test_category(test_path, description)
        except Exception as e:
            print(f"Error running {description}: {e}")
            results[description] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for desc, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        print(f"{status}: {desc}")
    
    print(f"\nTotal: {passed}/{total} test categories passing")
    print("\nNote: To fix failing tests:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Add provider configurations in api/main.py")
    print("3. Fix missing imports (Union in router.py)")
    print("4. Run external services (Redis, PostgreSQL)")

if __name__ == "__main__":
    main()