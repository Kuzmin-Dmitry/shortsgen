"""
Test script for ScenarioGenerator.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scenario_generator import ScenarioGenerator


def test_scenario_generator():
    """Test scenario generator functionality."""
    generator = ScenarioGenerator()
    
    print("=== Testing CreateVideo scenario ===")
    try:
        scenario = generator.create_video_scenario(
            description="Напиши короткий текст про кота",
            slides_count=3
        )
        
        print(f"Scenario ID: {scenario.scenario_id}")
        print(f"Tasks count: {len(scenario.tasks)}")
        
        for i, task in enumerate(scenario.tasks):
            print(f"Task {i+1}: {task.name} (id: {task.id[:8]}..., queue: {task.queue})")
            if task.consumers:
                print(f"  Consumers: {[c[:8] + '...' for c in task.consumers]}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing CreateVoice scenario ===")
    try:
        scenario = generator.create_voice_scenario(
            description="Это небольшой текст, который нужно озвучить"
        )
        
        print(f"Scenario ID: {scenario.scenario_id}")
        print(f"Tasks count: {len(scenario.tasks)}")
        
        for i, task in enumerate(scenario.tasks):
            print(f"Task {i+1}: {task.name} (id: {task.id[:8]}..., queue: {task.queue})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing CreateSlides scenario ===")
    try:
        scenario = generator.create_slides_scenario(
            base_prompt="Опиши содержание для слайда",
            slides_count=5
        )
        
        print(f"Scenario ID: {scenario.scenario_id}")
        print(f"Tasks count: {len(scenario.tasks)}")
        
        for i, task in enumerate(scenario.tasks):
            print(f"Task {i+1}: {task.name} (id: {task.id[:8]}..., queue: {task.queue})")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_scenario_generator()
