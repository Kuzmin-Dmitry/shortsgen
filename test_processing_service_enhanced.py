"""
Test script for Processing Service - CreateVideo scenario generation.
"""

import json
import requests
from datetime import datetime


def test_create_video_scenario():
    """Test CreateVideo scenario generation."""
    base_url = "http://localhost:8001"
    
    # Test data
    request_data = {
        "description": "Создай короткое видео про котов",
        "slides_count": 3,
        "metadata": {
            "priority": "high",
            "category": "pets"
        }
    }
    
    print("🚀 Testing CreateVideo scenario generation...")
    print(f"Request: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    try:
        # Create scenario
        response = requests.post(
            f"{base_url}/scenarios/create-video",
            json=request_data,
            timeout=30
        )
        
        print(f"\n📤 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Scenario created successfully!")
            print(f"📋 Scenario ID: {result['scenario_id']}")
            print(f"📊 Tasks created: {result['tasks_created']}")
            
            print("\n📝 Task Summary:")
            for task in result['tasks']:
                print(f"  • {task['service']}.{task['name']} [{task['status']}]")
            
            # Test getting scenario
            scenario_id = result['scenario_id']
            print(f"\n🔍 Testing scenario retrieval...")
            
            get_response = requests.get(f"{base_url}/scenarios/{scenario_id}")
            if get_response.status_code == 200:
                scenario_data = get_response.json()
                print(f"✅ Scenario retrieved: {len(scenario_data['tasks'])} tasks")
            else:
                print(f"❌ Failed to retrieve scenario: {get_response.status_code}")
                
        else:
            print(f"❌ Failed to create scenario")
            print(f"Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed. Make sure the processing service is running on port 8001")
        print("Run: cd processing_service && python app.py")
    except Exception as e:
        print(f"❌ Test failed: {e}")


def test_health_check():
    """Test health check endpoint."""
    base_url = "http://localhost:8001"
    
    print("\n🏥 Testing health check...")
    
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Service is healthy: {data.get('status', 'unknown')} at {data.get('ts', 'unknown')}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("PROCESSING SERVICE TEST")
    print("=" * 60)
    
    test_health_check()
    test_create_video_scenario()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETED")
    print("=" * 60)
