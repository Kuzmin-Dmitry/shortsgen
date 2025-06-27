"""
Test task status updates via API.
"""

import requests
import json
import time

def test_task_status_update():
    """Test updating task status through the API."""
    base_url = "http://localhost:8001"
    
    print("=== Testing Task Status Updates ===")
    
    # First generate a scenario to get task IDs
    print("1. Generating scenario to get task IDs...")
    payload = {
        "scenario": "CreateVideo", 
        "description": "Test scenario for status updates",
        "slides_count": 1
    }
    response = requests.post(f"{base_url}/generate", json=payload)
    
    if response.status_code != 201:
        print(f"Failed to generate scenario: {response.status_code}")
        return
        
    scenario_data = response.json()
    scenario_id = scenario_data["scenario_id"]
    print(f"Created scenario: {scenario_id}")
    
    # Get scenario details to find task IDs
    response = requests.get(f"{base_url}/scenarios/{scenario_id}")
    if response.status_code != 200:
        print(f"Failed to get scenario details: {response.status_code}")
        return
        
    scenario_details = response.json()
    tasks = scenario_details["tasks"]
    
    if not tasks:
        print("No tasks found in scenario")
        return
    
    # Pick the first task to test status updates
    task = tasks[0]
    task_id = task["id"]
    print(f"Testing with task: {task_id} ({task['name']})")
    
    # Test getting individual task status
    print("\n2. Getting individual task status...")
    response = requests.get(f"{base_url}/tasks/{task_id}")
    print(f"GET /tasks/{task_id} -> {response.status_code}")
    if response.status_code == 200:
        print(f"Task status: {response.json()['status']}")
    
    # Test updating task status
    print("\n3. Updating task status to 'processing'...")
    update_payload = {"status": "processing"}
    response = requests.patch(f"{base_url}/tasks/{task_id}/status", json=update_payload)
    print(f"PATCH /tasks/{task_id}/status -> {response.status_code}")
    
    if response.status_code == 200:
        print("Status updated successfully")
        
        # Verify the update
        response = requests.get(f"{base_url}/tasks/{task_id}")
        if response.status_code == 200:
            updated_status = response.json()["status"]
            print(f"Verified updated status: {updated_status}")
        
        # Check scenario progress
        response = requests.get(f"{base_url}/scenarios/{scenario_id}")
        if response.status_code == 200:
            progress = response.json()["progress"]
            print(f"Scenario progress: {progress}")
    
    # Test updating to 'success' with result
    print("\n4. Updating task status to 'success' with result...")
    update_payload = {
        "status": "success", 
        "result_ref": "test_result_reference_123"
    }
    response = requests.patch(f"{base_url}/tasks/{task_id}/status", json=update_payload)
    print(f"PATCH /tasks/{task_id}/status -> {response.status_code}")
    
    if response.status_code == 200:
        print("Status updated to success")
        
        # Final verification
        response = requests.get(f"{base_url}/tasks/{task_id}")
        if response.status_code == 200:
            task_data = response.json()
            print(f"Final task status: {task_data['status']}")
            print(f"Result reference: {task_data['result_ref']}")

if __name__ == "__main__":
    test_task_status_update()
