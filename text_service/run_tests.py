"""
Test runner for text-service - runs all tests in sequence.
"""

import asyncio
import subprocess
import sys
import os
from datetime import datetime


def print_header(title):
    """Print formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_section(title):
    """Print formatted section."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


async def run_test_file(test_file, description):
    """Run a specific test file."""
    print_section(f"Running {description}")
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Try to run the test file
        if test_file.endswith('.py'):
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(result.stdout)
                print(f"✅ {description} - PASSED")
                return True
            else:
                print(result.stdout)
                if result.stderr:
                    print("STDERR:", result.stderr)
                print(f"❌ {description} - FAILED")
                return False
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT (>30s)")
        return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False


def check_dependencies():
    """Check if required dependencies are available."""
    print_section("Checking Dependencies")
    
    required_packages = [
        ('fastapi', 'FastAPI web framework'),
        ('redis', 'Redis client'),
        ('openai', 'OpenAI API client'),
        ('pydantic', 'Data validation'),
        ('uvicorn', 'ASGI server')
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description} (MISSING)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies are available")
    return True


def check_environment():
    """Check environment configuration."""
    print_section("Checking Environment")
    
    env_vars = [
        ('OPENAI_API_KEY', 'OpenAI API key', False),  # False = not critical for basic tests
        ('REDIS_HOST', 'Redis host', False),
        ('REDIS_PORT', 'Redis port', False),
        ('OUTPUT_DIR', 'Output directory', False)
    ]
    
    for var, description, critical in env_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive values
            display_value = "***" if "KEY" in var or "PASSWORD" in var else value
            print(f"✅ {var} = {display_value}")
        else:
            status = "❌" if critical else "⚠️ "
            print(f"{status} {var} - {description} (not set)")
    
    print("✅ Environment check completed")
    return True


async def main():
    """Run all tests."""
    start_time = datetime.now()
    
    print_header("TEXT-SERVICE TEST RUNNER")
    print(f"Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Pre-flight checks
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        return
    
    check_environment()
    
    # Test files to run
    tests = [
        ("test_simple.py", "Basic Component Tests"),
        ("test_units.py", "Unit Tests"), 
        ("test_integration.py", "Integration Tests"),
        ("test_compatibility.py", "Compatibility Tests")
    ]
    
    # Results tracking
    results = []
    
    print_header("RUNNING TESTS")
    
    for test_file, description in tests:
        success = await run_test_file(test_file, description)
        results.append((test_file, description, success))
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    passed = sum(1 for _, _, success in results if success)
    total = len(results)
    
    for test_file, description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {description}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! 🎉")
        print("Text-service is ready for production!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Please review the failed tests above")
    
    end_time = datetime.now()
    duration = end_time - start_time
    print(f"\nTest run completed in {duration.total_seconds():.2f} seconds")
    
    # Quick start guide
    if passed == total:
        print_header("QUICK START GUIDE")
        print("1. Set environment variables:")
        print("   export OPENAI_API_KEY='your-api-key'")
        print("   export REDIS_HOST='localhost'  # if needed")
        print()
        print("2. Start Redis server:")
        print("   docker run -d -p 6379:6379 redis:latest")
        print()
        print("3. Start text-service:")
        print("   python app.py")
        print()
        print("4. Check health:")
        print("   curl http://localhost:8002/health")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
    except Exception as e:
        print(f"\n❌ Test runner error: {e}")
        import traceback
        traceback.print_exc()
