"""
Telephony Handler module for Tofia Voice Assistant.
Manages inbound and outbound calls using the Vapi.ai SDK.
"""
import logging
import config
import json
import requests

logger = logging.getLogger(__name__)

# Import real Vapi if not in mock mode
if hasattr(config, 'MOCK_MODE') and not config.MOCK_MODE:
    try:
        # Try to import the real Vapi SDK
        import vapi
        logger.info("Using real Vapi SDK")
    except ImportError:
        logger.warning("Real Vapi SDK not found, falling back to mock implementation")
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
        
        vapi = MockVapi
else:
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
    
    vapi = MockVapi


class TelephonyHandler:
    """Handles inbound and outbound calls through Vapi.ai."""
    
    def __init__(self):
        """Initialize the Vapi client."""
        self.vapi_client = vapi.Client(config.VAPI_API_KEY)
        self.api_base_url = "https://api.vapi.ai/call"  # Direct API endpoint for fallback
    
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
        if not to_number:
            logger.error("Cannot place call: 'to_number' is required")
            return None
            
        try:
            logger.info(f"Placing outbound call to {to_number}")
            
            # Clean patient info for logging - avoid PII in logs
            safe_patient_info = {k: "REDACTED" if k in ["name", "dob"] else v 
                                for k, v in patient_info.items() if v is not None}
            logger.info(f"Call context: {safe_patient_info}")
            
            # If we're in mock mode or using the mock Vapi SDK
            if (hasattr(config, 'MOCK_MODE') and config.MOCK_MODE) or not hasattr(vapi, 'Client'):
                mock_response = self.vapi_client.calls.create(
                    to=to_number,
                    from_=config.TOFIA_PHONE_NUMBER,
                    assistant_id="hospital_assistant",
                    config={
                        "temperature": config.TEMPERATURE,
                        "max_tokens": config.MAX_TOKENS,
                        "first_message": f"Hello, this is Tofia calling from the automated appointment scheduling service. I'd like to schedule an appointment for {patient_info.get('name', 'a patient')}.",
                        "webhook_url": f"{config.WEBHOOK_BASE_URL}/api/hospital_conversation",
                        "context": patient_info
                    },
                    status_callback=f"{config.WEBHOOK_BASE_URL}/api/call_status"
                )
                logger.info(f"MOCK call placed successfully, SID: {mock_response.call_sid}")
                return mock_response.call_sid
            else:
                # Attempt to use real Vapi SDK
                try:
                    call_response = self.vapi_client.calls.create(
                        to=to_number,
                        from_=config.TOFIA_PHONE_NUMBER,
                        assistant_id="hospital_assistant",
                        config={
                            "temperature": config.TEMPERATURE,
                            "max_tokens": config.MAX_TOKENS,
                            "first_message": f"Hello, this is Tofia calling from the automated appointment scheduling service. I'd like to schedule an appointment for {patient_info.get('name', 'a patient')}.",
                            "webhook_url": f"{config.WEBHOOK_BASE_URL}/api/hospital_conversation",
                            "context": patient_info
                        },
                        status_callback=f"{config.WEBHOOK_BASE_URL}/api/call_status"
                    )
                    logger.info(f"Call placed successfully, SID: {call_response.call_sid}")
                    return call_response.call_sid
                except Exception as sdk_error:
                    # If SDK fails, try direct API call as fallback
                    logger.warning(f"SDK call failed, trying direct API: {sdk_error}")
                    try:
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {config.VAPI_API_KEY}"
                        }
                        payload = {
                            "to": to_number,
                            "from": config.TOFIA_PHONE_NUMBER,
                            "assistant_id": "hospital_assistant",
                            "config": {
                                "temperature": config.TEMPERATURE,
                                "max_tokens": config.MAX_TOKENS,
                                "first_message": f"Hello, this is Tofia calling from the automated appointment scheduling service. I'd like to schedule an appointment for {patient_info.get('name', 'a patient')}.",
                                "webhook_url": f"{config.WEBHOOK_BASE_URL}/api/hospital_conversation",
                                "context": patient_info
                            },
                            "status_callback": f"{config.WEBHOOK_BASE_URL}/api/call_status"
                        }
                        response = requests.post(
                            f"{self.api_base_url}", 
                            headers=headers,
                            json=payload
                        )
                        if response.status_code == 200:
                            response_data = response.json()
                            logger.info(f"Call placed successfully via API, SID: {response_data.get('call_sid')}")
                            return response_data.get('call_sid')
                        else:
                            logger.error(f"API call failed: {response.status_code} - {response.text}")
                            return None
                    except Exception as api_error:
                        logger.error(f"Error with direct API call: {api_error}")
                        return None
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
        if not call_sid:
            logger.error("Cannot get transcript: 'call_sid' is required")
            return []
            
        try:
            # Mock or SDK implementation
            if (hasattr(config, 'MOCK_MODE') and config.MOCK_MODE) or not hasattr(vapi, 'Client'):
                transcript_response = self.vapi_client.calls.get_transcript(call_sid)
                return transcript_response.messages
            else:
                # Attempt to use real Vapi SDK 
                try:
                    transcript_response = self.vapi_client.calls.get_transcript(call_sid)
                    return transcript_response.messages
                except Exception as sdk_error:
                    # If SDK fails, try direct API call as fallback
                    logger.warning(f"SDK transcript retrieval failed, trying direct API: {sdk_error}")
                    try:
                        headers = {
                            "Authorization": f"Bearer {config.VAPI_API_KEY}"
                        }
                        response = requests.get(
                            f"{self.api_base_url}/{call_sid}/transcript", 
                            headers=headers
                        )
                        if response.status_code == 200:
                            return response.json().get('messages', [])
                        else:
                            logger.error(f"API transcript retrieval failed: {response.status_code} - {response.text}")
                            return []
                    except Exception as api_error:
                        logger.error(f"Error with direct API transcript retrieval: {api_error}")
                        return []
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
        if not call_sid:
            logger.error("Cannot end call: 'call_sid' is required")
            return False
            
        try:
            # Mock or SDK implementation
            if (hasattr(config, 'MOCK_MODE') and config.MOCK_MODE) or not hasattr(vapi, 'Client'):
                self.vapi_client.calls.end(call_sid)
                logger.info(f"MOCK call ended: {call_sid}")
                return True
            else:
                # Attempt to use real Vapi SDK
                try:
                    self.vapi_client.calls.end(call_sid)
                    logger.info(f"Call ended: {call_sid}")
                    return True
                except Exception as sdk_error:
                    # If SDK fails, try direct API call as fallback
                    logger.warning(f"SDK call end failed, trying direct API: {sdk_error}")
                    try:
                        headers = {
                            "Authorization": f"Bearer {config.VAPI_API_KEY}"
                        }
                        response = requests.post(
                            f"{self.api_base_url}/{call_sid}/end", 
                            headers=headers
                        )
                        if response.status_code == 200:
                            logger.info(f"Call ended via API: {call_sid}")
                            return True
                        else:
                            logger.error(f"API call end failed: {response.status_code} - {response.text}")
                            return False
                    except Exception as api_error:
                        logger.error(f"Error with direct API call end: {api_error}")
                        return False
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
