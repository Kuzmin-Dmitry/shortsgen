"""
Integration test for video service separation.
"""

import requests
import time
import json
import tempfile
import os
from pathlib import Path

def test_video_service_health():
    """Test video service health endpoint."""
    try:
        response = requests.get("http://localhost:8004/health", timeout=10)
        print(f"Video service health: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.json()}")
            return True
        return False
    except Exception as e:
        print(f"Video service health check failed: {e}")
        return False

def test_processing_service_health():
    """Test processing service health endpoint."""
    try:
        response = requests.get("http://localhost:8001/", timeout=10)
        print(f"Processing service health: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"Processing service health check failed: {e}")
        return False

def test_video_generation_flow():
    """Test the video generation flow through processing service."""
    try:
        # Start video generation
        response = requests.post(
            "http://localhost:8001/generate",
            json={"custom_prompt": "A short story about a cat"},
            timeout=10
        )
        
        print(f"Generate request: {response.status_code}")
        if response.status_code == 202:
            data = response.json()
            job_id = data["job_id"]
            print(f"Job ID: {job_id}")
            
            # Check job status
            for i in range(5):
                time.sleep(2)
                status_response = requests.get(f"http://localhost:8001/status/{job_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Job status: {status_data['status']}")
                    if status_data["status"] in ["completed", "failed"]:
                        return status_data["status"] == "completed"
                        
            return False
        return False
    except Exception as e:
        print(f"Video generation test failed: {e}")
        return False

def main():
    """Run integration tests."""
    print("=== Video Service Integration Tests ===")
    
    print("\n1. Testing video service health...")
    video_health = test_video_service_health()
    
    print("\n2. Testing processing service health...")
    processing_health = test_processing_service_health()
    
    if video_health and processing_health:
        print("\n3. Testing video generation flow...")
        generation_success = test_video_generation_flow()
        
        if generation_success:
            print("\n✅ All tests passed! Video service separation successful.")
        else:
            print("\n❌ Video generation test failed.")
    else:
        print("\n❌ Health checks failed. Services may not be running.")

if __name__ == "__main__":
    main()
