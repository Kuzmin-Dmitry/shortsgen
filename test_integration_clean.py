"""
Integration tests for the microservice architecture.

This module tests the communication between all services in the shortsgen application,
ensuring that the API Gateway, Processing Service, and Text Service work together correctly.
"""

import requests
import json
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTest:
    """Integration test suite for the shortsgen microservices."""
    
    def __init__(self, base_urls=None):
        """
        Initialize the integration test suite.
        
        Args:
            base_urls: Dictionary of service URLs, defaults to localhost ports
        """
        self.base_urls = base_urls or {
            'api_gateway': 'http://localhost:8000',
            'processing_service': 'http://localhost:8001', 
            'text_service': 'http://localhost:8002'
        }
        self.session = requests.Session()
        self.timeout = 30

    def test_health_endpoints(self):
        """Test that all services respond to health checks."""
        logger.info("Testing health endpoints...")
        
        results = {}
        for service, url in self.base_urls.items():
            try:
                response = self.session.get(f"{url}/health", timeout=self.timeout)
                if response.status_code == 200:
                    data = response.json()
                    results[service] = {
                        'status': 'healthy',
                        'response': data
                    }
                    logger.info(f"✅ {service} health check passed: {data}")
                else:
                    results[service] = {
                        'status': 'unhealthy',
                        'status_code': response.status_code
                    }
                    logger.error(f"❌ {service} health check failed: {response.status_code}")
            except Exception as e:
                results[service] = {
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"❌ {service} health check error: {e}")
        
        return results

    def test_text_service_direct(self):
        """Test the text service directly."""
        logger.info("Testing text service directly...")
        
        payload = {
            "prompt": "Write a brief test sentence about microservices.",
            "model": "openai",
            "max_tokens": 50
        }
        
        try:
            response = self.session.post(
                f"{self.base_urls['text_service']}/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"✅ Text service direct test passed: {data.get('success', False)}")
                return {
                    'status': 'success',
                    'content': data.get('content', ''),
                    'tokens': data.get('tokens_generated', 0)
                }
            else:
                logger.error(f"❌ Text service direct test failed: {response.status_code}")
                return {
                    'status': 'failed',
                    'status_code': response.status_code,
                    'response': response.text
                }
        except Exception as e:
            logger.error(f"❌ Text service direct test error: {e}")
            return {'status': 'error', 'error': str(e)}

    def test_end_to_end_generation(self):
        """Test end-to-end content generation through the API Gateway."""
        logger.info("Testing end-to-end generation through API Gateway...")
        
        payload = {
            "topic": "integration testing for microservices"
        }
        
        try:
            # Submit generation request
            response = self.session.post(
                f"{self.base_urls['api_gateway']}/generate",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 202:  # Accepted
                data = response.json()
                job_id = data.get('job_id')
                logger.info(f"✅ Job submitted successfully: {job_id}")
                
                # Check job status (wait a bit for processing)
                time.sleep(2)
                status_response = self.session.get(
                    f"{self.base_urls['api_gateway']}/status/{job_id}",
                    timeout=self.timeout
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    logger.info(f"✅ Job status retrieved: {status_data.get('status')}")
                    return {
                        'status': 'success',
                        'job_id': job_id,
                        'job_status': status_data.get('status'),
                        'submit_response': data,
                        'status_response': status_data
                    }
                else:
                    logger.warning(f"⚠️ Could not retrieve job status: {status_response.status_code}")
                    return {
                        'status': 'partial_success',
                        'job_id': job_id,
                        'submit_response': data,
                        'status_error': status_response.status_code
                    }
            else:
                logger.error(f"❌ End-to-end test failed: {response.status_code}")
                return {
                    'status': 'failed',
                    'status_code': response.status_code,
                    'response': response.text
                }
        except Exception as e:
            logger.error(f"❌ End-to-end test error: {e}")
            return {'status': 'error', 'error': str(e)}

    def run_all_tests(self):
        """Run all integration tests and return a summary."""
        logger.info("🧪 Starting integration test suite...")
        
        results = {
            'health_checks': self.test_health_endpoints(),
            'text_service_direct': self.test_text_service_direct(),
            'end_to_end': self.test_end_to_end_generation()
        }
        
        # Generate summary
        summary = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0
        }
        
        # Count health checks
        for service, health_result in results['health_checks'].items():
            summary['total_tests'] += 1
            if health_result.get('status') == 'healthy':
                summary['passed'] += 1
            elif health_result.get('status') == 'error':
                summary['errors'] += 1
            else:
                summary['failed'] += 1
        
        # Count other tests
        for test_name in ['text_service_direct', 'end_to_end']:
            summary['total_tests'] += 1
            result = results[test_name]
            if result.get('status') in ['success', 'partial_success']:
                summary['passed'] += 1
            elif result.get('status') == 'error':
                summary['errors'] += 1
            else:
                summary['failed'] += 1
        
        logger.info(f"🏁 Integration tests completed:")
        logger.info(f"   ✅ Passed: {summary['passed']}")
        logger.info(f"   ❌ Failed: {summary['failed']}")
        logger.info(f"   💥 Errors: {summary['errors']}")
        logger.info(f"   📊 Total: {summary['total_tests']}")
        
        return {
            'summary': summary,
            'results': results,
            'success': summary['failed'] == 0 and summary['errors'] == 0
        }

if __name__ == "__main__":
    # Run integration tests when script is executed directly
    test_suite = IntegrationTest()
    results = test_suite.run_all_tests()
    
    if results['success']:
        logger.info("🎉 All integration tests passed!")
        exit(0)
    else:
        logger.error("💥 Some integration tests failed!")
        exit(1)
