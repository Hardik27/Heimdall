"""
Direct test of the agentic health assistant.
This script bypasses the server and directly interacts with the workflow.
"""
import os
import sys
import logging
import json
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables directly from .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
load_dotenv(dotenv_path=env_path)

# Confirm API key is loaded
api_key = os.environ.get('OPENAI_API_KEY')
if api_key:
    logger.info(f"Using API key starting with: {api_key[:4]}***")
else:
    logger.error("No OpenAI API key found")
    sys.exit(1)

# Import workflow modules
from schema import AgentState, IntentType, ConversationMemory, UserProfile
from workflow import create_health_assistant_graph, initialize_agent_state

def test_agent(message, phone_number="+15551234567"):
    """Run a direct test of the agent workflow."""
    logger.info(f"Testing agent with message: '{message}'")
    
    # Create the workflow graph
    graph = create_health_assistant_graph()
    
    # Initialize state with user message
    state = initialize_agent_state(phone_number, message)
    
    # Process the message through the workflow
    logger.info("Running workflow...")
    try:
        for i, event in enumerate(graph.stream(state)):
            if 'current_agent' in event.data:
                logger.info(f"Step {i+1}: {event.data.get('current_agent')}")
                
        # Get final state
        final_state = graph.get_state()
        
        # Show results
        logger.info("-" * 80)
        logger.info("RESULTS:")
        logger.info(f"Intent: {final_state.current_intent}")
        logger.info(f"Response: {final_state.response_to_user}")
        
        if final_state.task_plan:
            logger.info(f"Task Plan: {final_state.task_plan.task_type}")
            logger.info("Steps:")
            for step in final_state.task_plan.steps:
                logger.info(f"  {step['step_number']}. {step['description']}")
                
        if final_state.appointment_details:
            logger.info(f"Appointment: {final_state.appointment_details}")
            
        logger.info("-" * 80)
        return True
    except Exception as e:
        logger.error(f"Error in workflow: {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the agentic health assistant directly")
    parser.add_argument("--message", default="I'd like to schedule a doctor appointment for my back pain", 
                      help="Test message to process")
    parser.add_argument("--phone", default="+15551234567", help="Test phone number")
    
    args = parser.parse_args()
    
    # Run the test
    test_agent(args.message, args.phone)
