"""
Utility module for file system operations.

This module provides helper functions for working with directories,
ensuring that the necessary directories exist before performing file operations.
"""

import os
import requests
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

def ensure_directory(path: str):
    """
    Ensures that the directory for the specified path exists.
    
    If the provided path points to a file (i.e., has a file extension),
    this function ensures that the parent directory exists.
    Otherwise, it treats the path as a directory and creates it if necessary.
    
    Parameters:
        path (str): A file or directory path.
    """
    directory = path
    if os.path.splitext(path)[1]:
        directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
