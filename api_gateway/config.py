"""
Configuration module for API Gateway.

This module contains only the configuration needed for the API Gateway service.
"""

import os
from typing import Final
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# URL of the processing service (api-gateway communicates with it)
PROCESSING_SERVICE_URL: Final[str] = os.getenv("PROCESSING_SERVICE_URL", "http://localhost:8001")


