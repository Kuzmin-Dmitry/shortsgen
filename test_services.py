#!/usr/bin/env python3
"""
Простой скрипт для тестирования processing-service.
"""

import requests
import json
import time


def test_processing_service():
    """Тестирование processing-service."""
    base_url = "http://localhost:8001"
    
    print("=== ТЕСТИРОВАНИЕ PROCESSING SERVICE ===")
    
    # 1. Health check
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # 2. Создание сценария
    print("\n=== СОЗДАНИЕ СЦЕНАРИЯ ===")
    scenario_data = {
        "scenario": "CreateVideo",
        "description": "Создай видео про котов",
        "slides_count": 3
    }
    
    try:
        response = requests.post(
            f"{base_url}/generate",
            json=scenario_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Создание сценария: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"  Scenario ID: {result.get('scenario_id')}")
            print(f"  Tasks created: {result.get('tasks_created')}")
            scenario_id = result.get('scenario_id')
            
            # 3. Мониторинг сценария
            print(f"\n=== МОНИТОРИНГ СЦЕНАРИЯ {scenario_id} ===")
            time.sleep(1)  # Даём время на обработку
            
            monitor_response = requests.get(f"{base_url}/scenarios/{scenario_id}")
            print(f"Мониторинг: {monitor_response.status_code}")
            
            if monitor_response.status_code == 200:
                scenario_info = monitor_response.json()
                print(f"  Статус: {scenario_info.get('status', 'unknown')}")
                tasks = scenario_info.get('tasks', [])
                print(f"  Задач: {len(tasks)}")
                
                for task in tasks:
                    print(f"    {task.get('id')}: {task.get('service')} - {task.get('name')} ({task.get('status')})")
            
        else:
            print(f"  Error: {response.text}")
            
    except Exception as e:
        print(f"Ошибка создания сценария: {e}")


def test_audio_service():
    """Тестирование audio-service."""
    base_url = "http://localhost:8003"
    
    print("\n=== ТЕСТИРОВАНИЕ AUDIO SERVICE ===")
    
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"Audio service недоступен: {e}")


if __name__ == "__main__":
    test_processing_service()
    test_audio_service()
