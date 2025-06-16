#!/usr/bin/env python3
"""
Test script to verify ShortsGen API functionality
"""

import requests
import time
import json

def test_api():
    """Test the ShortsGen API"""
    
    # API endpoints
    gateway_url = "http://localhost:8000"
    
    print("🧪 Testing ShortsGen API...")
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{gateway_url}/")
        if response.status_code == 200:
            print(f"✅ API Gateway is online: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API Gateway: {e}")
        return False
    
    # Test 2: Submit generation job
    print("\n2. Testing video generation job submission...")
    try:
        payload = {
            "custom_prompt": "Create an interesting story about artificial intelligence"
        }
        response = requests.post(f"{gateway_url}/generate", json=payload)
        if response.status_code == 202:
            job_data = response.json()
            job_id = job_data["job_id"]
            print(f"✅ Job submitted successfully: {job_data}")
        else:
            print(f"❌ Job submission failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Job submission error: {e}")
        return False
    
    # Test 3: Check job status
    print(f"\n3. Testing job status check (Job ID: {job_id})...")
    try:
        response = requests.get(f"{gateway_url}/status/{job_id}")
        if response.status_code == 200:
            status_data = response.json()
            print(f"✅ Job status retrieved: {status_data}")
        else:
            print(f"❌ Status check failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Status check error: {e}")
        return False
    
    print("\n🎉 All API tests passed! ShortsGen is working correctly.")
    print(f"\n📝 Job {job_id} is processing. Check status periodically with:")
    print(f"   GET {gateway_url}/status/{job_id}")
    
    return True

if __name__ == "__main__":
    test_api()
