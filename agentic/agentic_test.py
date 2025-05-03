"""
Test script for the agentic health assistant that ensures
we're using the API key from the agentic/.env file.
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get absolute path to agentic directory and .env file
AGENTIC_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(AGENTIC_DIR, '.env')

# Ensure we're using the agentic/.env file
logger.info(f"Loading environment variables from: {ENV_PATH}")
load_dotenv(dotenv_path=ENV_PATH, override=True)

# Make sure the API key is set in the environment
api_key = os.environ.get('OPENAI_API_KEY')
if not api_key:
    logger.error(f"No API key found in {ENV_PATH}")
    sys.exit(1)

logger.info(f"API key loaded successfully: {api_key[:8]}***")

# Force using gpt-3.5-turbo instead of gpt-4o to avoid quota issues
GPT_MODEL = "gpt-3.5-turbo"  # Force cheaper model with higher quota
logger.info(f"Using model: {GPT_MODEL}")

# Import our dependencies
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # Set up a simple test using the API key
    llm = ChatOpenAI(
        model=GPT_MODEL,
        temperature=0.7,
        api_key=api_key
    )
    
    # Run a simple test query
    logger.info("Sending test query to OpenAI API...")
    messages = [
        SystemMessage(content="You are a helpful health assistant."),
        HumanMessage(content="Hello, I need to schedule a doctor's appointment.")
    ]
    
    response = llm.invoke(messages)
    
    logger.info("API response received successfully!")
    logger.info(f"Response: {response.content[:100]}...")
    
    logger.info("API key is working correctly!")
    
except Exception as e:
    logger.error(f"Error testing OpenAI API: {e}")
    sys.exit(1)

if __name__ == "__main__":
    # If we got here, the API key is working
    logger.info("Test completed successfully.")
