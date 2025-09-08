"""
Configuration settings for the Intelligent Chat Interface
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# AI Provider Configuration
# PROVIDER can be: "openai", "ollama", or "openrouter". Default: openrouter
AI_PROVIDER = os.getenv("AI_PROVIDER", "openrouter").lower()

# Ollama Configuration (used when AI_PROVIDER=="ollama")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")

# OpenRouter Configuration (used when AI_PROVIDER=="openrouter")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openrouter/auto")
OPENROUTER_API_URL = os.getenv(
    "OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions"
)
OPENROUTER_SITE_URL = os.getenv("OPENROUTER_SITE_URL", "http://localhost:8501")
OPENROUTER_APP_TITLE = os.getenv("OPENROUTER_APP_TITLE", "Intelligent Chat Interface")

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
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
MAX_TOKENS = 2000
TEMPERATURE = 0.7
