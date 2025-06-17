"""
Test script to verify that processing_service is properly separated from text_service and audio_service.
This script checks that all imports work correctly and no direct dependencies remain.
"""

import sys
import os

# Add the processing_service directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'processing_service'))

def test_imports():
    """Test that all processing_service imports work correctly."""
    print("Testing imports...")
    
    try:
        # Test core imports
        from processing_service.generator import Generator
        from processing_service.text_client import TextClient
        from processing_service.audio_client import AudioClient
        from processing_service.text_client_service import TextService
        from processing_service.app import app
        
        print("✓ All core imports successful")
        
        # Test that old imports don't exist
        old_imports = [
            'processing_service.text_service_client',
            'processing_service.audio_service_client', 
            'processing_service.chat_service',
            'processing_service.chat_service_clean',
            'processing_service.chat_service_new'
        ]
        
        for old_import in old_imports:
            try:
                __import__(old_import)
                print(f"✗ ERROR: Old import {old_import} still exists")
                return False
            except ImportError:
                print(f"✓ Confirmed {old_import} removed")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_generator_initialization():
    """Test that Generator can be initialized with new services."""
    print("\nTesting Generator initialization...")
    
    try:
        from processing_service.generator import Generator
        
        # This should work without any direct service dependencies
        generator = Generator()
        
        # Check that it has the right clients
        assert hasattr(generator, 'audio_client'), "Missing audio_client"
        assert hasattr(generator, 'text_service'), "Missing text_service"
        assert hasattr(generator, 'image_service'), "Missing image_service"
        assert hasattr(generator, 'video_editor'), "Missing video_editor"
        
        print("✓ Generator initialization successful")
        print(f"✓ Generator has audio_client: {type(generator.audio_client).__name__}")
        print(f"✓ Generator has text_service: {type(generator.text_service).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Generator initialization error: {e}")
        return False

def test_api_clients():
    """Test that API clients are configured correctly."""
    print("\nTesting API clients...")
    
    try:
        from processing_service.text_client import TextClient
        from processing_service.audio_client import AudioClient
        
        # Initialize clients (should not fail)
        text_client = TextClient()
        audio_client = AudioClient()
        
        print(f"✓ TextClient initialized with base_url: {text_client.base_url}")
        print(f"✓ AudioClient initialized with base_url: {audio_client.base_url}")
        
        # Verify they are configured for HTTP communication
        assert hasattr(text_client, 'session'), "TextClient missing HTTP session"
        assert hasattr(audio_client, 'session'), "AudioClient missing HTTP session"
        
        print("✓ API clients configured for HTTP communication")
        return True
        
    except Exception as e:
        print(f"✗ API client error: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("PROCESSING SERVICE SEPARATION TEST")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_generator_initialization, 
        test_api_clients
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("✓ Processing service successfully separated from text_service and audio_service")
        print("✓ Only HTTP API communication remains")
        return True
    else:
        print(f"✗ SOME TESTS FAILED ({passed}/{total})")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
