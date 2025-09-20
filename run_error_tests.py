#!/usr/bin/env python3
"""
Simple script to run error handling tests.
"""

import subprocess
import sys
import time
import os

def main():
    """Run error handling tests."""
    print("🚀 Starting Task Planner Agent Error Handling Tests")
    print("=" * 60)
    
    # Check if server is running
    print("1. Checking if server is running...")
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        print("Please start the server first with: python main.py")
        return False
    
    # Run the error handling tests
    print("\n2. Running error handling tests...")
    try:
        result = subprocess.run([
            sys.executable, "test_error_handling.py"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ Error handling tests completed successfully")
            return True
        else:
            print(f"❌ Error handling tests failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ Error handling tests timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
