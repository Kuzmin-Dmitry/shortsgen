"""
Simple test for processing-service API.
"""

import requests
import json
import time

def test_api():
    """Test processing service API endpoints."""
    base_url = "http://localhost:8001"
    
    print("=== Testing Processing Service API ===")
    
    # Test root endpoint
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{base_url}/")
        print(f"GET / -> {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test health endpoint  
    print("\n2. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"GET /health -> {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test scenario generation (without Redis - will fail, but structure should work)
    print("\n3. Testing scenario generation...")
    try:
        payload = {
            "scenario": "CreateVideo", 
            "description": "Тестовый кот",
            "slides_count": 2
        }
        response = requests.post(f"{base_url}/generate", json=payload)
        print(f"POST /generate -> {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 201:
            scenario_data = response.json()
            scenario_id = scenario_data.get("scenario_id")
            
            # Test get scenario status
            print(f"\n4. Testing scenario status...")
            response = requests.get(f"{base_url}/scenarios/{scenario_id}")
            print(f"GET /scenarios/{scenario_id} -> {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
