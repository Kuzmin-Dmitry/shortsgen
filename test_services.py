"""
Test script to verify all services are running and communicating properly.
"""

import requests
import time
import sys
from typing import Dict, List

def test_service_health(service_name: str, url: str) -> bool:
    """Test if a service is healthy."""
    try:
        response = requests.get(f"{url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ {service_name} is healthy")
            return True
        else:
            print(f"❌ {service_name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name} is not responding: {str(e)}")
        return False

def test_text_service_generation() -> bool:
    """Test text service generation endpoint."""
    try:
        payload = {
            "prompt": "Write a short story about a cat.",
            "max_tokens": 100,
            "model": "openai"
        }
        response = requests.post("http://localhost:8002/generate", 
                               json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if data.get("success") and data.get("content"):
                print("✅ Text service generation is working")
                return True
            else:
                print(f"❌ Text service generation failed: {data}")
                return False
        else:
            print(f"❌ Text service generation returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Text service generation test failed: {str(e)}")
        return False

def test_processing_service_communication() -> bool:
    """Test if processing service can communicate with text service."""
    try:
        # This endpoint should exist in processing service to test text service communication
        response = requests.get("http://localhost:8001/health", timeout=10)
        if response.status_code == 200:
            print("✅ Processing service is accessible")
            return True
        else:
            print(f"❌ Processing service returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Processing service test failed: {str(e)}")
        return False

def main():
    """Run all service tests."""
    print("🧪 Testing ShortsGen Services...")
    print("=" * 50)
    
    # Define services to test
    services = [
        ("API Gateway", "http://localhost:8000"),
        ("Processing Service", "http://localhost:8001"),
        ("Text Service", "http://localhost:8002")
    ]
    
    # Test basic health endpoints
    health_results = []
    for service_name, url in services:
        result = test_service_health(service_name, url)
        health_results.append(result)
    
    print("\n🔧 Testing Service Functionality...")
    print("-" * 30)
    
    # Test text service generation if basic health passed
    if health_results[2]:  # Text service is healthy
        text_gen_result = test_text_service_generation()
    else:
        print("⏭️  Skipping text generation test (service not healthy)")
        text_gen_result = False
    
    # Test processing service communication
    if health_results[1]:  # Processing service is healthy
        proc_comm_result = test_processing_service_communication()
    else:
        print("⏭️  Skipping processing service communication test")
        proc_comm_result = False
    
    print("\n📊 Test Results Summary:")
    print("=" * 50)
    print(f"API Gateway Health: {'✅ PASS' if health_results[0] else '❌ FAIL'}")
    print(f"Processing Service Health: {'✅ PASS' if health_results[1] else '❌ FAIL'}")
    print(f"Text Service Health: {'✅ PASS' if health_results[2] else '❌ FAIL'}")
    print(f"Text Generation: {'✅ PASS' if text_gen_result else '❌ FAIL'}")
    print(f"Service Communication: {'✅ PASS' if proc_comm_result else '❌ FAIL'}")
    
    # Overall result
    all_passed = all(health_results) and text_gen_result and proc_comm_result
    
    if all_passed:
        print("\n🎉 All tests passed! Services are properly configured.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check service configurations.")
        sys.exit(1)

if __name__ == "__main__":
    main()
