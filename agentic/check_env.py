"""
Simple script to check the environment variables and OpenAI API key.
This will help diagnose issues with API key loading.
"""
import os
import sys
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_env():
    """Check environment variables and .env file."""
    logger.info(f"Current directory: {os.getcwd()}")
    
    # Check .env in current directory
    env_path = os.path.join(os.getcwd(), '.env')
    if os.path.exists(env_path):
        logger.info(f".env file found in current directory: {env_path}")
        with open(env_path, 'r') as f:
            first_line = f.readline().strip()
            logger.info(f"First line: {first_line[:20]}...")
    else:
        logger.info(f".env file NOT found in current directory")
    
    # Check .env in agentic directory
    agentic_env_path = os.path.join(os.getcwd(), 'agentic', '.env')
    if os.path.exists(agentic_env_path):
        logger.info(f".env file found in agentic directory: {agentic_env_path}")
        with open(agentic_env_path, 'r') as f:
            first_line = f.readline().strip()
            logger.info(f"First line: {first_line[:20]}...")
    else:
        logger.info(f".env file NOT found in agentic directory")
    
    # Load from current directory
    load_dotenv()
    api_key = os.environ.get('OPENAI_API_KEY', 'NOT_FOUND')
    if api_key != 'NOT_FOUND':
        logger.info(f"OPENAI_API_KEY from env: {api_key[:4]}...")
    else:
        logger.info("OPENAI_API_KEY not found in environment")
    
    # Try direct loading from agentic directory
    if os.path.exists(agentic_env_path):
        load_dotenv(dotenv_path=agentic_env_path)
        api_key = os.environ.get('OPENAI_API_KEY', 'NOT_FOUND')
        if api_key != 'NOT_FOUND':
            logger.info(f"OPENAI_API_KEY from agentic/.env: {api_key[:4]}...")
        else:
            logger.info("OPENAI_API_KEY not found in agentic/.env")
    
    # Try directly setting a test key
    test_key = "sk-test-key-12345"
    os.environ['OPENAI_API_KEY'] = test_key
    api_key = os.environ.get('OPENAI_API_KEY', 'NOT_FOUND')
    logger.info(f"OPENAI_API_KEY after direct setting: {api_key}")
    
    # Import modules to check their API key handling
    sys.path.append('agentic')
    try:
        from agents.base_agent import BaseAgent
        logger.info("Successfully imported BaseAgent")
    except Exception as e:
        logger.error(f"Error importing BaseAgent: {e}")

if __name__ == '__main__':
    check_env()
