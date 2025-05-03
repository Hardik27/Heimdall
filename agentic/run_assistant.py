"""
Direct test script for the Agentic Health Assistant.
This script uses direct imports to run a simple test conversation.
"""
import sys
import logging
import json
import os
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add paths for both local and parent modules
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)  # First check current directory
sys.path.insert(0, project_root)  # Then check project root

# Ask user for OpenAI API key if not set
openai_key = os.environ.get('OPENAI_API_KEY')
if not openai_key:
    print("OpenAI API key not found in environment variables.")
    print("Please enter your OpenAI API key:")
    openai_key = input("> ").strip()
    os.environ['OPENAI_API_KEY'] = openai_key

# Explicitly set in our config module
import config
config.OPENAI_API_KEY = openai_key

# Import necessary modules
try:
    from schema import IntentType, UserProfile, ConversationMemory, AgentState
    from workflow import create_health_assistant_graph, initialize_agent_state
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you're running this script from the project root directory.")
    sys.exit(1)

def run_conversation(phone_number: str, message: str) -> Dict[str, Any]:
    """
    Run a test conversation with the health assistant.
    
    Args:
        phone_number: The user's phone number
        message: The user's message
        
    Returns:
        Dict: The results of the conversation
    """
    print("-" * 80)
    print(f"Starting conversation with message: '{message}' from {phone_number}")
    print("-" * 80)
    
    # Create the workflow graph
    try:
        graph = create_health_assistant_graph()
        
        # Initialize the state
        state = initialize_agent_state(phone_number, message)
        
        # Process through the workflow
        print("Workflow Progress:")
        for i, event in enumerate(graph.stream(state)):
            if 'current_agent' in event.data:
                print(f"{i+1}. Agent: {event.data.get('current_agent')}")
        
        # Get the final state
        final_state = graph.get_state()
        
        # Print the response
        print("\nAssistant Response:")
        print("-" * 80)
        print(final_state.response_to_user)
        print("-" * 80)
        
        # Print additional information if available
        if final_state.current_intent:
            print(f"Detected Intent: {final_state.current_intent}")
        
        if final_state.task_plan:
            print("\nTask Plan:")
            print(f"- Task ID: {final_state.task_plan.task_id}")
            print(f"- Task Type: {final_state.task_plan.task_type}")
            print(f"- Status: {final_state.task_plan.status}")
            print("- Steps:")
            for step in final_state.task_plan.steps:
                print(f"  {step['step_number']}. {step['description']}")
        
        if final_state.appointment_details:
            print("\nAppointment Details:")
            apt = final_state.appointment_details
            print(f"- Doctor: {apt.doctor_name}")
            print(f"- Date: {apt.date}")
            print(f"- Time: {apt.time}")
            print(f"- Status: {apt.status}")
        
        print("-" * 80)
        
        return {
            "success": True,
            "response": final_state.response_to_user,
            "intent": str(final_state.current_intent) if final_state.current_intent else None,
            "conversation_completed": final_state.completed
        }
        
    except Exception as e:
        logger.error(f"Error in conversation: {e}")
        print(f"\nError: {e}")
        print("-" * 80)
        
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run the Agentic Health Assistant")
    parser.add_argument("--phone", default="+1234567890", help="Phone number to use for testing")
    parser.add_argument("--message", required=True, help="Message to process")
    
    args = parser.parse_args()
    
    # Run the conversation
    result = run_conversation(args.phone, args.message)
    
    # Print a summary
    if result.get("success"):
        print("Conversation completed successfully!")
    else:
        print(f"Conversation failed: {result.get('error')}")
