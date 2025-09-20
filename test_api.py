#!/usr/bin/env python3
"""
Test script for the Task Planner Agent FastAPI server.
This script tests the /plan endpoint to help debug issues.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_GOAL = "Learn Python programming and build a web application"

def test_server_connection():
    """Test if the server is running and accessible."""
    print("🔍 Testing server connection...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"✅ Server is running - Status: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Overall Status: {health_data.get('status', 'unknown')}")
            
            # Display service status
            services = health_data.get('services', {})
            print("   Service Status:")
            for service_name, service_info in services.items():
                status = service_info.get('status', 'unknown')
                service_type = service_info.get('type', 'Unknown')
                message = service_info.get('message', 'No message')
                print(f"     • {service_name}: {status} ({service_type}) - {message}")
            
            # Display environment status
            environment = health_data.get('environment', {})
            print("   Environment Variables:")
            for var_name, var_status in environment.items():
                print(f"     • {var_name}: {var_status}")
            
            # Display errors if any
            errors = health_data.get('errors', [])
            if errors:
                print("   Errors:")
                for error in errors:
                    print(f"     • {error}")
            
            # Display recommendations
            summary = health_data.get('summary', {})
            recommendations = summary.get('recommendations', [])
            if recommendations:
                print("   Recommendations:")
                for rec in recommendations:
                    print(f"     • {rec}")
            
            # Display summary
            if 'summary' in health_data:
                summary = health_data['summary']
                print(f"   Summary: {summary.get('healthy_services', 0)}/{summary.get('total_services', 0)} services healthy")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running or not accessible")
        print("   Make sure to start the server with: python main.py")
        return False
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_plan_endpoint():
    """Test the /plan POST endpoint."""
    print(f"\n🎯 Testing /plan endpoint with goal: '{TEST_GOAL}'")
    
    # Prepare the request data
    request_data = {
        "goal": TEST_GOAL,
        "start_date": datetime.now().strftime("%Y-%m-%d"),
        "save_to_db": True
    }
    
    print(f"📤 Sending request data: {json.dumps(request_data, indent=2)}")
    
    try:
        # Send the request
        response = requests.post(
            f"{BASE_URL}/plan",
            json=request_data,
            headers={"Content-Type": "application/json"},
            timeout=60  # 60 second timeout for AI generation
        )
        
        print(f"\n📊 Response Status: {response.status_code}")
        print(f"📊 Response Headers: {dict(response.headers)}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print(f"📊 Response Content (JSON):")
            print(json.dumps(response_data, indent=2))
            
            # Analyze the response
            if response_data.get('success'):
                print("\n✅ SUCCESS: Plan created successfully!")
                print(f"   Plan ID: {response_data.get('plan_id', 'None')}")
                print(f"   Message: {response_data.get('message', 'No message')}")
                
                # Check if formatted plan exists
                formatted_plan = response_data.get('formatted_plan')
                if formatted_plan:
                    print(f"   Formatted Plan Length: {len(formatted_plan)} characters")
                    print(f"   Formatted Plan Preview: {formatted_plan[:200]}...")
                else:
                    print("   ⚠️  No formatted plan in response")
                
                # Check if plan data exists
                plan_data = response_data.get('plan_data')
                if plan_data:
                    print(f"   Plan Data Keys: {list(plan_data.keys())}")
                    if 'daily_breakdown' in plan_data:
                        print(f"   Daily Breakdown Days: {len(plan_data['daily_breakdown'])}")
                else:
                    print("   ⚠️  No plan data in response")
                    
            else:
                print("\n❌ FAILURE: Plan creation failed!")
                print(f"   Error: {response_data.get('message', 'Unknown error')}")
                print(f"   Success: {response_data.get('success', 'Unknown')}")
                
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error: {e}")
            print(f"📊 Raw Response Content:")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("\n⏰ TIMEOUT: Request took too long (>60 seconds)")
        print("   This might indicate the AI service is slow or not responding")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Could not connect to server")
        print("   Make sure the server is running on http://localhost:8000")
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        print(f"   Error type: {type(e).__name__}")

def test_plans_endpoint():
    """Test the /plans GET endpoint."""
    print(f"\n📋 Testing /plans endpoint...")
    
    try:
        response = requests.get(f"{BASE_URL}/plans", timeout=10)
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ Plans retrieved successfully!")
            print(f"   Success: {response_data.get('success', 'Unknown')}")
            print(f"   Message: {response_data.get('message', 'No message')}")
            print(f"   Total Plans: {response_data.get('total_count', 0)}")
            print(f"   Plans Data: {len(response_data.get('plans', []))} plans")
        else:
            print(f"❌ Failed to retrieve plans - Status: {response.status_code}")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing /plans endpoint: {e}")

def test_invalid_requests():
    """Test the endpoint with invalid data to check error handling."""
    print(f"\n🧪 Testing error handling with invalid requests...")
    
    # Test 1: Empty goal
    print("\n1. Testing empty goal...")
    try:
        response = requests.post(
            f"{BASE_URL}/plan",
            json={"goal": "", "save_to_db": False},
            timeout=10
        )
        response_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {response_data.get('success', 'Unknown')}")
        print(f"   Message: {response_data.get('message', 'No message')}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Test 2: Invalid date format
    print("\n2. Testing invalid date format...")
    try:
        response = requests.post(
            f"{BASE_URL}/plan",
            json={"goal": "Test goal", "start_date": "invalid-date", "save_to_db": False},
            timeout=10
        )
        response_data = response.json()
        print(f"   Status: {response.status_code}")
        print(f"   Success: {response_data.get('success', 'Unknown')}")
        print(f"   Message: {response_data.get('message', 'No message')}")
    except Exception as e:
        print(f"   Error: {e}")

def main():
    """Main test function."""
    print("🚀 Task Planner Agent API Test Script")
    print("=" * 50)
    
    # Test server connection
    if not test_server_connection():
        print("\n❌ Cannot proceed with tests - server is not accessible")
        sys.exit(1)
    
    # Test plans endpoint first (simpler test)
    test_plans_endpoint()
    
    # Test plan creation
    test_plan_endpoint()
    
    # Test error handling
    test_invalid_requests()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")
    print("\nIf you see 'Error: undefined' in the frontend, check:")
    print("1. Server logs for detailed error messages")
    print("2. Network tab in browser developer tools")
    print("3. Console errors in browser developer tools")
    print("4. Make sure GEMINI_API_KEY is set in your environment")

if __name__ == "__main__":
    main()
