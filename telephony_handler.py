"""
Telephony Handler module for Tofia Voice Assistant.
Manages inbound and outbound calls using the Vapi.ai SDK.
"""
import logging
import config

logger = logging.getLogger(__name__)

# Mock Vapi implementation for demonstration purposes
class MockVapi:
    """Mock implementation of Vapi SDK for demonstration."""
    
    class Client:
        def __init__(self, api_key):
            self.api_key = api_key
            self.calls = self.Calls()
        
        class Calls:
            def create(self, **kwargs):
                logger.info(f"MOCK: Creating outbound call with parameters: {kwargs}")
                return type('obj', (object,), {'call_sid': 'mock-call-sid-123456'})
            
            def get_transcript(self, call_sid):
                logger.info(f"MOCK: Getting transcript for call {call_sid}")
                return type('obj', (object,), {'messages': [
                    {"role": "assistant", "content": "Hello, how can I help you?"},
                    {"role": "user", "content": "I need to schedule an appointment."}
                ]})
            
            def end(self, call_sid):
                logger.info(f"MOCK: Ending call {call_sid}")
                return True

# Use mock Vapi implementation
vapi = MockVapi


class TelephonyHandler:
    """Handles inbound and outbound calls through Vapi.ai."""
    
    def __init__(self):
        """Initialize the Vapi client."""
        # Replace with actual Vapi initialization
        self.vapi_client = vapi.Client(config.VAPI_API_KEY)
    
    def handle_inbound_call(self, call_data):
        """
        Handle an incoming call webhook from Vapi.
        
        Args:
            call_data: Call data from Vapi webhook
            
        Returns:
            dict: Response for Vapi containing instructions
        """
        call_sid = call_data.get("call_sid")
        phone_number = call_data.get("from")
        
        logger.info(f"Handling inbound call from {phone_number}, SID: {call_sid}")
        
        # Return configuration for Vapi
        return {
            "assistant_id": "patient_assistant",  # ID for patient persona in Vapi
            "config": {
                "temperature": config.TEMPERATURE,
                "max_tokens": config.MAX_TOKENS,
                "first_message": "Hello, this is Tofia, your healthcare assistant. How can I help you today?",
                "webhook_url": f"{config.WEBHOOK_BASE_URL}/api/patient_conversation",
            }
        }
    
    def place_outbound_call(self, to_number, patient_info):
        """
        Place an outbound call to a hospital.
        
        Args:
            to_number: The phone number to call
            patient_info: Information about the patient
            
        Returns:
            str: Call SID if successful, None otherwise
        """
        try:
            logger.info(f"Placing outbound call to {to_number}")
            
            # Example Vapi call (placeholder - replace with actual API call)
            call_response = self.vapi_client.calls.create(
                to=to_number,
                from_=config.TOFIA_PHONE_NUMBER,
                assistant_id="hospital_assistant",  # ID for hospital persona in Vapi
                config={
                    "temperature": config.TEMPERATURE,
                    "max_tokens": config.MAX_TOKENS,
                    "first_message": f"Hello, this is Tofia calling from the automated appointment scheduling service. I'd like to schedule an appointment for {patient_info.get('name', 'a patient')}.",
                    "webhook_url": f"{config.WEBHOOK_BASE_URL}/api/hospital_conversation",
                    "context": patient_info  # Pass patient info to the assistant
                },
                status_callback=config.CALL_STATUS_WEBHOOK
            )
            
            return call_response.call_sid
        
        except Exception as e:
            logger.error(f"Error placing outbound call: {e}")
            return None
    
    def get_call_transcript(self, call_sid):
        """
        Retrieve the transcript for a completed call.
        
        Args:
            call_sid: The Vapi call identifier
            
        Returns:
            list: List of transcript messages if successful, empty list otherwise
        """
        try:
            # Example Vapi transcript retrieval (placeholder)
            transcript_response = self.vapi_client.calls.get_transcript(call_sid)
            return transcript_response.messages
        
        except Exception as e:
            logger.error(f"Error retrieving call transcript: {e}")
            return []
            
    def end_call(self, call_sid):
        """
        End an active call.
        
        Args:
            call_sid: The Vapi call identifier
            
        Returns:
            bool: Success status of the operation
        """
        try:
            # Example Vapi call termination (placeholder)
            self.vapi_client.calls.end(call_sid)
            logger.info(f"Call ended: {call_sid}")
            return True
        
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
    
    def simulate_hospital_conversation(self, patient_info):
        """
        Simulate a conversation with a hospital receptionist for testing purposes.
        
        Args:
            patient_info: Information about the patient
            
        Returns:
            dict: Simulated appointment details
        """
        logger.info("Simulating hospital conversation")
        
        # Create hospital agent
        from conversation_agents import HospitalAgent
        hospital_agent = HospitalAgent(patient_info)
        
        # Simulate receptionist responses
        responses = [
            "Hello, General Hospital reception, how can I help you?",
            f"Alright, I can help schedule an appointment for {patient_info.get('name')}. What's the reason for the visit?",
            f"I see. And what's the patient's date of birth and insurance provider?",
            "We have an opening tomorrow at 2:30 PM with Dr. Smith or Friday at 10:00 AM with Dr. Johnson. Which would work better?",
            "Great, I've scheduled the appointment with Dr. Smith for tomorrow at 2:30 PM. Is there anything else you need?"
        ]
        
        # Process each response
        for response in responses:
            hospital_agent.generate_response(response)
        
        # Return simulated appointment details
        return {
            "date": "tomorrow",
            "time": "2:30 PM",
            "doctor_name": "Dr. Smith",
            "patient_name": patient_info.get("name", "Patient")
        }
