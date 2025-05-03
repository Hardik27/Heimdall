"""
Main entry point for the Agentic Health Assistant.
Integrates the LangGraph workflow with telephony and notifications.
"""
import sys
import logging
import json
import uuid
import os
from typing import Dict, List, Optional, Any, Union

# Add parent directory to path to import from our own modules
sys.path.append('.')
sys.path.append('..')
sys.path.append(sys.path[0])
# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import directly from local modules
from workflow import create_health_assistant_graph, initialize_agent_state
from schema import AgentState

# Import from existing codebase
from telephony_handler import TelephonyHandler
from sms_notifications import send_sms_notification
import config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthAssistant:
    """
    Main class for integrating the agentic workflow with external systems.
    """
    
    def __init__(self):
        """Initialize the Health Assistant with its workflow."""
        self.graph = create_health_assistant_graph()
        self.telephony_handler = TelephonyHandler()
        self.active_conversations = {}  # Track active conversations by ID
    
    def process_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an inbound call from Vapi.
        
        Args:
            call_data: Call data from the Vapi webhook
            
        Returns:
            dict: Response for Vapi with instructions
        """
        # Extract relevant information
        call_sid = call_data.get('call_id') or call_data.get('call_sid')
        phone_number = call_data.get('from') or call_data.get('customer', {}).get('number')
        message = call_data.get('input') or call_data.get('transcript', {}).get('text', '')
        
        logger.info(f"Processing inbound call from {phone_number}: {message[:30]}...")
        
        # Check if this is a new or existing conversation
        conversation_id = self._get_conversation_id(call_sid)
        
        if conversation_id in self.active_conversations:
            # Continue existing conversation
            state = self.active_conversations[conversation_id]
            state.user_input = message
        else:
            # Start new conversation
            state = initialize_agent_state(phone_number, message)
            self.active_conversations[conversation_id] = state
        
        # Process through the workflow
        try:
            for event in self.graph.stream(state):
                if 'current_agent' in event.data:
                    logger.info(f"Agent transition: {event.data['current_agent']}")
            
            # Get the final state
            final_state = self.graph.get_state()
            self.active_conversations[conversation_id] = final_state
            
            # Generate response for Vapi
            response = {
                "actions": [
                    {
                        "say": final_state.response_to_user
                    }
                ]
            }
            
            # If the conversation is complete, clean up
            if final_state.completed:
                # Send SMS if we have appointment details
                if final_state.appointment_details:
                    self._send_appointment_confirmation(phone_number, final_state)
                
                # Remove from active conversations
                self.active_conversations.pop(conversation_id, None)
                
                # Add hangup action if appropriate
                response["actions"].append({"hangup": {}})
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing call: {e}")
            # Return an error response
            return {
                "actions": [
                    {
                        "say": "I'm sorry, I experienced a technical issue. Please try your call again in a moment."
                    },
                    {"hangup": {}}
                ]
            }
    
    def place_outbound_call(self, phone_number: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Place an outbound call using the telephony handler.
        
        Args:
            phone_number: The phone number to call
            context: Optional context for the call
            
        Returns:
            Dict or None: Call information if successful
        """
        return self.telephony_handler.place_outbound_call(phone_number, context)
    
    def _get_conversation_id(self, call_sid: str) -> str:
        """
        Generate a consistent conversation ID from a call SID.
        
        Args:
            call_sid: The call SID from Vapi
            
        Returns:
            str: A conversation ID
        """
        # For simplicity, use the call_sid as the conversation ID
        return f"conv-{call_sid}"
    
    def _send_appointment_confirmation(self, phone_number: str, state: AgentState) -> bool:
        """
        Send an SMS confirmation for an appointment.
        
        Args:
            phone_number: The user's phone number
            state: The final agent state
            
        Returns:
            bool: Success status
        """
        if not state.appointment_details:
            return False
            
        apt = state.appointment_details
        message = (
            f"Your appointment with {apt.doctor_name} is confirmed for "
            f"{apt.date} at {apt.time}. "
            f"Location: {apt.facility_name or 'Medical Office'}. "
            f"Reply YES to confirm or call us to reschedule."
        )
        
        return send_sms_notification(phone_number, message)


# Singleton instance
health_assistant = HealthAssistant()

def handle_vapi_webhook(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for Vapi webhooks.
    
    Args:
        request_data: The webhook request data
        
    Returns:
        dict: Response for Vapi
    """
    return health_assistant.process_inbound_call(request_data)


if __name__ == "__main__":
    # For testing purposes
    import argparse
    
    parser = argparse.ArgumentParser(description="Agentic Health Assistant")
    parser.add_argument("--phone", help="Phone number to simulate a call from")
    parser.add_argument("--message", help="Message to process")
    
    args = parser.parse_args()
    
    if args.phone and args.message:
        # Simulate an inbound call
        mock_call_data = {
            "call_id": f"test-{uuid.uuid4().hex[:8]}",
            "from": args.phone,
            "input": args.message
        }
        
        response = health_assistant.process_inbound_call(mock_call_data)
        print(json.dumps(response, indent=2))
    else:
        print("Usage: python health_assistant.py --phone +1234567890 --message 'Hello, I need help'")
