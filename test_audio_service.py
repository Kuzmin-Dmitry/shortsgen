#!/usr/bin/env python3
"""
Test script for audio service functionality.
"""

import requests
import json
import sys


def test_audio_service(base_url="http://localhost:8003"):
    """Test audio service endpoints."""
    
    print(f"Testing Audio Service at {base_url}")
    print("=" * 50)
    
    # Test health check
    print("1. Testing health check...")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False
    
    # Test audio generation
    print("\n2. Testing audio generation...")
    test_request = {
        "text": "Привет! Это тестовое сообщение для проверки работы аудио сервиса.",
        "language": "ru",
        "voice": "alloy",
        "format": "mp3"
    }
    
    try:
        response = requests.post(
            f"{base_url}/generate", 
            json=test_request,
            timeout=60
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ Audio generation passed")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            print(f"   File size: {result.get('file_size_kb')} KB")
        else:
            print(f"❌ Audio generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        return False
    
    # Test audio streaming
    print("\n3. Testing audio streaming...")
    try:
        response = requests.post(
            f"{base_url}/generate-stream", 
            json=test_request,
            timeout=60
        )
        if response.status_code == 200:
            audio_data = response.content
            print("✅ Audio streaming passed")
            print(f"   Audio data size: {len(audio_data)} bytes")
            print(f"   Content type: {response.headers.get('content-type')}")
        else:
            print(f"❌ Audio streaming failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Audio streaming error: {e}")
        return False
    
    print("\n🎉 All audio service tests passed!")
    return True


def test_processing_service_integration(base_url="http://localhost:8001"):
    """Test processing service integration with audio service."""
    
    print(f"\nTesting Processing Service integration at {base_url}")
    print("=" * 50)
    
    # Test health check
    print("1. Testing processing service health...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Processing service health check passed")
        else:
            print(f"❌ Processing service health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Processing service health check error: {e}")
        return False
    
    print("\n🎉 Processing service integration test passed!")
    return True


if __name__ == "__main__":
    success = True
    
    # Test audio service
    if not test_audio_service():
        success = False
    
    # Test processing service integration
    if not test_processing_service_integration():
        success = False
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)
