"""
Test script for new processing service architecture.
"""

import sys
import os
import logging

# Add the processing_service directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_text_service():
    """Test the TextService module."""
    try:
        from text_service import TextService, ModelResponse
        logger.info("✅ TextService import successful")
        
        # Test initialization
        text_service = TextService()
        logger.info("✅ TextService initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ TextService test failed: {e}")
        return False

def test_workflow_orchestrator():
    """Test the WorkflowOrchestrator module."""
    try:
        from workflow_orchestrator import WorkflowOrchestrator, GenerationStrategy
        logger.info("✅ WorkflowOrchestrator import successful")
        
        # Test initialization
        orchestrator = WorkflowOrchestrator()
        logger.info("✅ WorkflowOrchestrator initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ WorkflowOrchestrator test failed: {e}")
        return False

def test_content_generator():
    """Test the ContentGenerator module."""
    try:
        from content_generator import ContentGenerator
        logger.info("✅ ContentGenerator import successful")
        
        # Test initialization
        generator = ContentGenerator()
        logger.info("✅ ContentGenerator initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ ContentGenerator test failed: {e}")
        return False

def test_media_processor():
    """Test the MediaProcessor module."""
    try:
        from media_processor import MediaProcessor
        logger.info("✅ MediaProcessor import successful")
        
        # Test initialization
        processor = MediaProcessor()
        logger.info("✅ MediaProcessor initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ MediaProcessor test failed: {e}")
        return False

def test_generator_compatibility():
    """Test the legacy Generator compatibility."""
    try:
        from generator import Generator
        logger.info("✅ Generator import successful")
        
        # Test initialization
        generator = Generator()
        logger.info("✅ Generator initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ Generator test failed: {e}")
        return False

def test_resilience():
    """Test the resilience module."""
    try:
        from resilience import with_retry, RetryConfig, CircuitBreaker, CircuitBreakerConfig
        logger.info("✅ Resilience module import successful")
        
        # Test configurations
        retry_config = RetryConfig(max_attempts=3)
        circuit_config = CircuitBreakerConfig()
        circuit_breaker = CircuitBreaker(circuit_config)
        
        logger.info("✅ Resilience components initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ Resilience test failed: {e}")
        return False

def test_workflow_state():
    """Test the workflow state module."""
    try:
        from workflow_state import WorkflowState, StageResult, StageStatus, WorkflowResult
        logger.info("✅ WorkflowState import successful")
        
        # Test initialization
        state = WorkflowState()
        result = StageResult("test", StageStatus.COMPLETED)
        workflow_result = WorkflowResult(success=True)
        
        logger.info("✅ WorkflowState components initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ WorkflowState test failed: {e}")
        return False

def test_enhanced_config():
    """Test the enhanced configuration module."""
    try:
        from enhanced_config import ConfigManager, ApplicationConfig
        logger.info("✅ Enhanced config import successful")
        
        # Test initialization
        config_manager = ConfigManager()
        logger.info("✅ Enhanced config initialization successful")
        
        return True
    except Exception as e:
        logger.error(f"❌ Enhanced config test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🚀 Starting Processing Service Architecture Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Text Service", test_text_service),
        ("Workflow Orchestrator", test_workflow_orchestrator),
        ("Content Generator", test_content_generator),
        ("Media Processor", test_media_processor),
        ("Generator Compatibility", test_generator_compatibility),
        ("Resilience", test_resilience),
        ("Workflow State", test_workflow_state),
        ("Enhanced Config", test_enhanced_config),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Testing {test_name}...")
        if test_func():
            passed += 1
    
    logger.info("\n" + "=" * 60)
    logger.info(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Architecture improvements successful.")
        return True
    else:
        logger.warning(f"⚠️  {total - passed} tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
