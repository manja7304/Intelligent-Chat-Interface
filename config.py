"""
Configuration settings for the Intelligent Chat Interface
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# LinkedIn Configuration
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")

# SerpAPI Configuration
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "")

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///candidate_database.db")

# Application Configuration
APP_TITLE = "Intelligent Chat Interface for HR Candidate Profiling"
APP_VERSION = "1.0.0"

# File paths
SAMPLE_RESUME_PATH = "data/sample_resume.pdf"
SAMPLE_FORM_TEMPLATE_PATH = "data/sample_hr_form.json"
EXPORT_DIRECTORY = "exports"

# AI Model Configuration
DEFAULT_MODEL = "gpt-3.5-turbo"
MAX_TOKENS = 2000
TEMPERATURE = 0.7
