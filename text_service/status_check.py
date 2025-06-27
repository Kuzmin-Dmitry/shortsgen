"""
Quick status check for text-service.
"""

import sys
import os


def check_files():
    """Check if all required files exist."""
    required_files = [
        'app.py',
        'config.py', 
        'models.py',
        'task_handler.py',
        'text_generator.py',
        'requirements.txt',
        'README.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    return True


def check_imports():
    """Check if key modules can be imported."""
    try:
        from models import Task, TaskStatus
        from config import REDIS_URL, TEXT_QUEUE
        from task_handler import TaskHandler
        from text_generator import GetTextOpenAI
        from app import app
        
        print("✅ All modules import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def check_model_structure():
    """Check model structure."""
    try:
        from models import Task, TaskStatus
        
        # Test TaskStatus enum
        statuses = [TaskStatus.PENDING, TaskStatus.QUEUED, TaskStatus.PROCESSING, 
                   TaskStatus.SUCCESS, TaskStatus.FAILED]
        assert len(statuses) == 5
        
        # Test Task model
        task = Task(
            id="test",
            scenario_id="test",
            service="text-service", 
            name="CreateText"
        )
        assert hasattr(task, 'prompt')
        assert hasattr(task, 'consumers')
        assert hasattr(task, 'params')
        
        print("✅ Model structure is correct")
        return True
    except Exception as e:
        print(f"❌ Model structure error: {e}")
        return False


def main():
    """Quick status check."""
    print("🔍 Text-Service Quick Status Check")
    print("=" * 40)
    
    checks = [
        ("File Check", check_files),
        ("Import Check", check_imports),
        ("Model Check", check_model_structure)
    ]
    
    passed = 0
    for name, check_func in checks:
        print(f"\n{name}:")
        if check_func():
            passed += 1
    
    print(f"\n📊 Result: {passed}/{len(checks)} checks passed")
    
    if passed == len(checks):
        print("\n🎉 TEXT-SERVICE STATUS: READY! 🎉")
        print("\nNext steps:")
        print("1. Run: python run_tests.py  # Full test suite")
        print("2. Run: python app.py       # Start service")
        print("3. Test: curl http://localhost:8002/health")
    else:
        print("\n⚠️  TEXT-SERVICE STATUS: ISSUES DETECTED")
        print("Please fix the issues above before running")
    
    return passed == len(checks)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
