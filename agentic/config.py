"""
Configuration settings for the Agentic Health Assistant system.
"""
import sys
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path to access main config
sys.path.append('..')
sys.path.append('.')

# Load OpenAI API key directly from environment
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

# Make sure this value is explicitly set and not empty
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in environment variables or .env file")

# Set the API key in the os.environ to ensure it's available for the SDK
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# Telephony settings (with mock values for development)
MOCK_MODE = os.environ.get('MOCK_MODE', 'false').lower() == 'true'  # Parse from environment, default to False
VAPI_API_KEY = os.environ.get('VAPI_API_KEY', 'mock_vapi_key')
VAPI_ASSISTANT_ID = os.environ.get('VAPI_ASSISTANT_ID', 'mock_assistant_id')
VAPI_PHONE_NUMBER_ID = os.environ.get('VAPI_PHONE_NUMBER_ID', 'mock_phone_id')

# Twilio settings (with mock values for development)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', 'mock_account_sid')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', 'mock_auth_token')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER', '+10000000000')

# LLM Settings
GPT_MODEL = os.environ.get('GPT_MODEL', 'gpt-4-0125-preview')
LLM_MODEL = GPT_MODEL
LLM_TEMPERATURE = 0.7

# Agent Configuration
AGENT_CONCURRENCY = 1  # Number of concurrent conversations to process
MEMORY_TTL_MINUTES = 30  # Time to live for conversation memory

# Workflow Settings
DEFAULT_WORKFLOW = "health_assistant"
MAX_STEPS_PER_WORKFLOW = 20  # Maximum steps to prevent infinite loops

# Database Settings
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///health_assistant.db')

# Feature Flags
USE_STREAMING = True  # Whether to use streaming responses
ENABLE_TASK_EXECUTION = True  # Whether to enable task execution agent

# Agentic System Settings
USE_AGENTIC_SYSTEM = True  # Feature flag for the agentic system
AGENTIC_ROLLOUT_PERCENT = int(os.environ.get('AGENTIC_ROLLOUT_PERCENT', 100))  # Percentage of calls to route to agentic system

# Export settings to be used by the system
def get_settings() -> Dict[str, Any]:
    """Get all configuration settings as a dictionary."""
    settings = {}
    for key in dir():
        if key.isupper() and not key.startswith('__'):
            settings[key] = globals()[key]
    return settings
