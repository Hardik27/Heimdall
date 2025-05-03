"""
Telephony Handler module for Tofia Voice Assistant.
Manages inbound and outbound calls using the Vapi.ai SDK.
"""
import logging
import config
import json
import requests
import os
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Try to import Vapi SDK, but it's optional
try:
    import vapi
    VAPI_SDK_AVAILABLE = True
    logger.info("Vapi SDK imported successfully")
except ImportError:
    VAPI_SDK_AVAILABLE = False
    logger.warning("Real Vapi SDK not found, falling back to mock implementation")

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
            """Mock implementation of Vapi SDK client."""
            
            class Client:
                def __init__(self, api_key=None):
                    self.api_key = api_key
                    self.calls = self.Calls()
                
                def create_phone_call(self, **kwargs):
                    """
                    Create an outbound phone call according to Vapi documentation.
                    
                    Args:
                        to (str): The phone number to call
                        from (str): The phone number to call from
                        webhook_url (str): The URL to receive events
                        assistant (dict): Assistant configuration
                        metadata (dict, optional): Additional context for the call
                        
                    Returns:
                        object: A mock response object with call_id
                    """
                    to = kwargs.get('to')
                    from_number = kwargs.get('from')
                    webhook_url = kwargs.get('webhook_url')
                    assistant = kwargs.get('assistant', {})
                    metadata = kwargs.get('metadata', {})
                    
                    logger.info(f"MOCK MODE: Creating outbound call from {from_number} to {to}")
                    logger.info(f"MOCK MODE: Assistant config: {assistant.get('name', 'Unnamed')}")
                    
                    # Create a mock call_id
                    call_id = f"MOCK_CALL_{int(time.time())}"
                    
                    # Create a mock response object
                    response = type('obj', (object,), {
                        'call_id': call_id,
                        'status': 'queued',
                        'to': to,
                        'from': from_number,
                        'webhook_url': webhook_url,
                        'metadata': metadata
                    })
                    
                    return response
                
                class Calls:
                    def __init__(self):
                        self.active_calls = {}
                    
                    def create(self, to=None, from_=None, webhook_url=None, context=None, **kwargs):
                        """
                        Legacy method for creating an outbound call.
                        For compatibility with old code.
                        
                        Args:
                            to: The phone number to call
                            from_: The phone number to call from
                            webhook_url: The URL to call when events happen
                            context: Additional context for the call
                            
                        Returns:
                            dict: A mock call response with call_sid
                        """
                        logger.warning("DEPRECATED: Using legacy calls.create() method. Use create_phone_call() instead.")
                        call_sid = f"MOCK_CALL_{int(time.time())}"
                        logger.info(f"MOCK MODE: Creating call from {from_} to {to} with SID {call_sid}")
                        
                        # Store call data
                        self.active_calls[call_sid] = {
                            "to": to,
                            "from": from_,
                            "webhook_url": webhook_url,
                            "context": context,
                            "status": "queued",
                            "created_at": datetime.utcnow()
                        }
                        
                        return {"call_sid": call_sid, "status": "queued"}
                    
                    def get(self, call_sid):
                        """
                        Get information about a call.
                        
                        Args:
                            call_sid: The call SID
                            
                        Returns:
                            dict: Call information
                        """
                        if call_sid in self.active_calls:
                            return self.active_calls[call_sid]
                        return {"error": "Call not found"}
                    
                    def send_message(self, call_sid, text):
                        """
                        Send a message to a call.
                        
                        Args:
                            call_sid: The call SID
                            text: The text message to send
                            
                        Returns:
                            dict: Response with success status
                        """
                        logger.info(f"MOCK MODE: Sending message to call {call_sid}: {text[:30]}...")
                        
                        if call_sid in self.active_calls:
                            # In a real implementation, this would send a message to the call
                            # For now, just log it
                            if "messages" not in self.active_calls[call_sid]:
                                self.active_calls[call_sid]["messages"] = []
                            
                            self.active_calls[call_sid]["messages"].append({
                                "text": text,
                                "timestamp": datetime.utcnow()
                            })
                            
                            return {"success": True, "message": "Message sent successfully"}
                        
                        return {"success": False, "error": "Call not found"}
                    
                    def get_transcript(self, call_sid):
                        """
                        Get the transcript for a call.
                        
                        Args:
                            call_sid: The call SID
                            
                        Returns:
                            dict: Transcript information
                        """
                        if call_sid in self.active_calls:
                            return {"messages": self.active_calls[call_sid].get("messages", [])}
                        return {"error": "Call not found"}
                    
                    def end(self, call_sid):
                        """
                        End a call.
                        
                        Args:
                            call_sid: The call SID
                            
                        Returns:
                            bool: Success status
                        """
                        if call_sid in self.active_calls:
                            self.active_calls[call_sid]["status"] = "ended"
                            return True
                        return False
        
        vapi = MockVapi
else:
    # Mock Vapi implementation for demonstration purposes
    class MockVapi:
        """Mock implementation of Vapi SDK client."""
        
        class Client:
            def __init__(self, api_key=None):
                self.api_key = api_key
                self.calls = self.Calls()
            
            def create_phone_call(self, **kwargs):
                """
                Create an outbound phone call according to Vapi documentation.
                
                Args:
                    to (str): The phone number to call
                    from (str): The phone number to call from
                    webhook_url (str): The URL to receive events
                    assistant (dict): Assistant configuration
                    metadata (dict, optional): Additional context for the call
                    
                Returns:
                    object: A mock response object with call_id
                """
                to = kwargs.get('to')
                from_number = kwargs.get('from')
                webhook_url = kwargs.get('webhook_url')
                assistant = kwargs.get('assistant', {})
                metadata = kwargs.get('metadata', {})
                
                logger.info(f"MOCK MODE: Creating outbound call from {from_number} to {to}")
                logger.info(f"MOCK MODE: Assistant config: {assistant.get('name', 'Unnamed')}")
                
                # Create a mock call_id
                call_id = f"MOCK_CALL_{int(time.time())}"
                
                # Create a mock response object
                response = type('obj', (object,), {
                    'call_id': call_id,
                    'status': 'queued',
                    'to': to,
                    'from': from_number,
                    'webhook_url': webhook_url,
                    'metadata': metadata
                })
                
                return response
            
            class Calls:
                def __init__(self):
                    self.active_calls = {}
                
                def create(self, to=None, from_=None, webhook_url=None, context=None, **kwargs):
                    """
                    Legacy method for creating an outbound call.
                    For compatibility with old code.
                    
                    Args:
                        to: The phone number to call
                        from_: The phone number to call from
                        webhook_url: The URL to call when events happen
                        context: Additional context for the call
                        
                    Returns:
                        dict: A mock call response with call_sid
                    """
                    logger.warning("DEPRECATED: Using legacy calls.create() method. Use create_phone_call() instead.")
                    call_sid = f"MOCK_CALL_{int(time.time())}"
                    logger.info(f"MOCK MODE: Creating call from {from_} to {to} with SID {call_sid}")
                    
                    # Store call data
                    self.active_calls[call_sid] = {
                        "to": to,
                        "from": from_,
                        "webhook_url": webhook_url,
                        "context": context,
                        "status": "queued",
                        "created_at": datetime.utcnow()
                    }
                    
                    return {"call_sid": call_sid, "status": "queued"}
                
                def get(self, call_sid):
                    """
                    Get information about a call.
                    
                    Args:
                        call_sid: The call SID
                        
                    Returns:
                        dict: Call information
                    """
                    if call_sid in self.active_calls:
                        return self.active_calls[call_sid]
                    return {"error": "Call not found"}
                
                def send_message(self, call_sid, text):
                    """
                    Send a message to a call.
                    
                    Args:
                        call_sid: The call SID
                        text: The text message to send
                        
                    Returns:
                        dict: Response with success status
                    """
                    logger.info(f"MOCK MODE: Sending message to call {call_sid}: {text[:30]}...")
                    
                    if call_sid in self.active_calls:
                        # In a real implementation, this would send a message to the call
                        # For now, just log it
                        if "messages" not in self.active_calls[call_sid]:
                            self.active_calls[call_sid]["messages"] = []
                        
                        self.active_calls[call_sid]["messages"].append({
                            "text": text,
                            "timestamp": datetime.utcnow()
                        })
                        
                        return {"success": True, "message": "Message sent successfully"}
                    
                    return {"success": False, "error": "Call not found"}
                
                def get_transcript(self, call_sid):
                    """
                    Get the transcript for a call.
                    
                    Args:
                        call_sid: The call SID
                        
                    Returns:
                        dict: Transcript information
                    """
                    if call_sid in self.active_calls:
                        return {"messages": self.active_calls[call_sid].get("messages", [])}
                    return {"error": "Call not found"}
                
                def end(self, call_sid):
                    """
                    End a call.
                    
                    Args:
                        call_sid: The call SID
                        
                    Returns:
                        bool: Success status
                    """
                    if call_sid in self.active_calls:
                        self.active_calls[call_sid]["status"] = "ended"
                        return True
                    return False
    
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
    
    def place_outbound_call(self, phone_number, context=None):
        """
        Place an outbound call to a specified phone number following Vapi documentation.
        
        Args:
            phone_number: The phone number to call
            context: Additional context to pass to the call
            
        Returns:
            dict: Call information including call_sid if successful, None otherwise
        """
        logger.info(f"Placing outbound call to {phone_number}")
        
        # In mock mode, just return a fake call SID
        if hasattr(config, 'MOCK_MODE') and config.MOCK_MODE:
            fake_call_sid = f"MOCK_CALL_{int(time.time())}"
            logger.info(f"MOCK MODE: Simulated outbound call with SID: {fake_call_sid}")
            return {"call_sid": fake_call_sid, "status": "queued"}
        
        try:
            # Make the API call to Vapi
            url = "https://api.vapi.ai/call/phone"
            headers = {
                "Authorization": f"Bearer {config.VAPI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Use the most basic format possible
            data = {
                "assistantId": "Tofia",
                "phoneNumberId": "70cedc36-4d83-4256-afda-69f282085f10",
                "customer": {
                    "number": phone_number  # Use the phone number passed to the function instead of hardcoding
                }
            }
            
            # Add metadata if context is provided
            if context:
                data["metadata"] = context
            
            logger.info(f"Making Vapi API call with payload: {data}")
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Outbound call placed successfully via API: {response_data.get('id', 'Unknown ID')}")
                # Convert call_id to call_sid for consistency
                return {"call_sid": response_data.get('id'), "status": "queued"}
            else:
                logger.error(f"API call failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error placing outbound call: {e}")
            return None
    
    def send_message_to_call(self, call_sid, message):
        """
        Send a message to an active call.
        
        Args:
            call_sid: The call SID
            message: The message to send
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Sending message to call {call_sid}: {message[:30]}...")
        
        # In mock mode, just log the message
        if hasattr(config, 'MOCK_MODE') and config.MOCK_MODE:
            logger.info(f"MOCK MODE: Message to call {call_sid}: {message}")
            return True
        
        try:
            # Make the API call to Vapi
            url = f"https://api.vapi.ai/call/{call_sid}/send-text"
            headers = {
                "Authorization": f"Bearer {config.VAPI_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {"text": message}
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to call {call_sid} via direct API")
                return True
            else:
                logger.error(f"Failed to send message to call {call_sid}: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error sending message to call: {e}")
            return False
    
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
            # Make the API call to Vapi
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
            # Make the API call to Vapi
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
