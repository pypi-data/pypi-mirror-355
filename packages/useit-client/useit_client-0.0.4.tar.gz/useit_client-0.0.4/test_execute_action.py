#!/usr/bin/env python3
"""
Test script for the new execute_action API endpoint.
This demonstrates how to send direct action execution requests.
"""

import requests
import json
import time

def test_execute_action(port=7888, host="localhost"):
    """Test the execute_action endpoint with a sample action."""
    
    url = f"http://{host}:{port}/execute_action"
    
    # Sample action data - adjust based on your TeachmodeExecutor requirements
    test_action = {
        "action": {
            "action": "screenshot",
            "coordinate": [100, 100]
        },
        "selected_screen": 0,
        "full_screen_game_mode": 0,
        "user_id": "test_user",
        "trace_id": "test_trace_001"
    }
    
    print(f"Sending action to {url}")
    print(f"Action data: {json.dumps(test_action, indent=2)}")
    
    try:
        response = requests.post(url, json=test_action, timeout=30)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Content: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Action executed successfully!")
            print(f"Status: {result.get('status')}")
            print(f"Results: {result.get('results')}")
            print(f"Message: {result.get('message')}")
        else:
            print(f"\n❌ Action failed with status {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request failed: {e}")

def test_status_endpoint(port=7888, host="localhost"):
    """Test the status endpoint to verify the server is ready."""
    
    url = f"http://{host}:{port}/status"
    
    print(f"Checking status at {url}")
    
    try:
        response = requests.get(url, timeout=10)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            status = response.json()
            print("✅ Server is ready!")
            print(f"Mode: {status.get('mode')}")
            print(f"Ready: {status.get('ready')}")
            print(f"User ID: {status.get('user_id')}")
            print(f"Trace ID: {status.get('trace_id')}")
            return True
        else:
            print(f"❌ Status check failed: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Status request failed: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the execute_action API")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=7888, help="Server port")
    parser.add_argument("--action-only", action="store_true", help="Skip status check")
    
    args = parser.parse_args()
    
    print("🚀 Testing Direct Execution API")
    print("=" * 50)
    
    if not args.action_only:
        print("1. Checking server status...")
        if not test_status_endpoint(args.port, args.host):
            print("Server not ready. Make sure the useit-client is running.")
            exit(1)
        
        print("\n" + "=" * 50)
    
    print("2. Testing execute_action endpoint...")
    test_execute_action(args.port, args.host)
    
    print("\n" + "=" * 50)
    print("✅ Test completed!") 