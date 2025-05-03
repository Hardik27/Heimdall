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

# Try to import Vapi SDK but don't fail if not available
try:
    import vapi
    VAPI_SDK_AVAILABLE = True
    logger.info("Vapi SDK imported successfully")
except ImportError:
    VAPI_SDK_AVAILABLE = False
    logger.warning("Vapi SDK not found. Using fallback implementation for local development.")
    
    # Define a MockVapi class that works with our custom agents
    class MockVapi:
        """Fallback implementation of Vapi SDK client for local development."""
        
        class Client:
            def __init__(self, api_key=None):
                self.api_key = api_key
                logger.info("Initialized MockVapi Client with API key")
    
    # Use the mock class as the vapi module when not available
    vapi = MockVapi

class TelephonyHandler:
    """Handles inbound and outbound calls through Vapi.ai."""
    
    def __init__(self):
        """Initialize the Vapi client."""
        self.vapi_client = vapi.Client(config.VAPI_API_KEY)
        self.api_base_url = "https://api.vapi.ai/call"  # Direct API endpoint
    
    def handle_inbound_call(self, call_data):
        """
        Handle an incoming call webhook from Vapi.
        
        Args:
            call_data: Call data from Vapi webhook
            
        Returns:
            dict: Response for Vapi containing instructions
        """
        logger.info(f"Handling incoming call from {call_data.get('from', 'unknown')}")
        
        # Updated configuration to use Vapi's built-in LLM
        response = {
            # Configure the assistant to use Vapi's built-in LLM
            "assistant": {
                "name": "Tofia Health Assistant",
                "firstMessage": "Hello, this is Tofia Health Assistant. How can I help you today?",
                "voiceId": "shimmer"  # You can choose a different voice if preferred
            },
            # Still define functions for specific actions if needed
            "functions": [
                {
                    "name": "transfer_to_webhook",
                    "description": "Transfer control to our custom webhook",
                    "parameters": {}
                }
            ],
            # We still want to receive updates for tracking purposes
            "statusCallback": f"{config.WEBHOOK_BASE_URL}/call_status",
            "recording": {
                "enabled": True
            }
            # Remove the disableAssistant flag
        }
        
        logger.info(f"Returning Vapi configuration: {json.dumps(response, indent=2)}")
        return response
    
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
        
        # If we're in fallback mode, return a mock call_sid
        if not VAPI_SDK_AVAILABLE:
            mock_call_sid = f"MOCK_CALL_{int(time.time())}"
            logger.info(f"Fallback mode: Generating mock call SID: {mock_call_sid}")
            return {"call_sid": mock_call_sid, "status": "queued"}
        
        try:
            # Make the API call to Vapi with updated structure
            url = "https://api.vapi.ai/call/phone"
            headers = {
                "Authorization": f"Bearer {config.VAPI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            # Updated configuration for the outbound call to use Vapi's built-in LLM
            data = {
                "phoneNumberId": config.VAPI_PHONE_NUMBER_ID,
                "customer": {
                    "number": phone_number
                },
                # Configure the assistant to use Vapi's built-in LLM
                "assistant": {
                    "name": "Tofia Health Assistant",
                    "firstMessage": "Hello, this is Tofia Health Assistant. How can I help you today?",
                    "voiceId": "shimmer"  # You can choose a different voice if preferred
                },
                # Still define functions for specific actions if needed
                "functions": [
                    {
                        "name": "transfer_to_webhook",
                        "description": "Transfer control to our custom webhook",
                        "parameters": {}
                    }
                ],
                "statusCallback": f"{config.WEBHOOK_BASE_URL}/call_status",
                "recording": {
                    "enabled": True
                }
                # Remove the disableAssistant flag
            }
            
            # Add metadata if context is provided
            if context:
                data["metadata"] = context
            
            logger.info(f"Making Vapi API call with payload: {json.dumps(data, indent=2)}")
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
        
        # In fallback mode, just log the message
        if not VAPI_SDK_AVAILABLE:
            logger.info(f"Fallback mode: Would send message to call {call_sid}: {message[:100]}")
            return True
        
        try:
            # Use Vapi API to send a message to the call
            url = f"{self.api_base_url}/{call_sid}/send-message"
            headers = {
                "Authorization": f"Bearer {config.VAPI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "content": message
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"Message sent successfully to call {call_sid}")
                return True
            else:
                logger.error(f"Failed to send message: {response.status_code} - {response.text}")
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
        logger.info(f"Retrieving transcript for call {call_sid}")
        
        # In fallback mode, return an empty transcript
        if not VAPI_SDK_AVAILABLE:
            logger.info(f"Fallback mode: No transcript available for call {call_sid}")
            return []
        
        try:
            # Use Vapi API to get the transcript
            url = f"{self.api_base_url}/{call_sid}/transcript"
            headers = {
                "Authorization": f"Bearer {config.VAPI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                transcript_data = response.json()
                logger.info(f"Retrieved transcript for call {call_sid}")
                return transcript_data.get("messages", [])
            else:
                logger.error(f"Failed to get transcript: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting call transcript: {e}")
            return []
    
    def end_call(self, call_sid):
        """
        End an active call.
        
        Args:
            call_sid: The Vapi call identifier
            
        Returns:
            bool: Success status of the operation
        """
        logger.info(f"Ending call {call_sid}")
        
        # In fallback mode, just log the action
        if not VAPI_SDK_AVAILABLE:
            logger.info(f"Fallback mode: Would end call {call_sid}")
            return True
        
        try:
            # Use Vapi API to end the call
            url = f"{self.api_base_url}/{call_sid}/hang-up"
            headers = {
                "Authorization": f"Bearer {config.VAPI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers)
            
            if response.status_code == 200:
                logger.info(f"Successfully ended call {call_sid}")
                return True
            else:
                logger.error(f"Failed to end call: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
