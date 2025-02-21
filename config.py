# config.py

import os
from dotenv import load_dotenv

load_dotenv()

DEEPAI_API_KEY = os.getenv("DEEPAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")