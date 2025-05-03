#!/usr/bin/env python
"""
Test script for direct hospital calling using the phone number from .env.
This tests making an outbound call to the hospital number without database lookup.
"""
import logging
import time
import os
from datetime import datetime
from voice_assistant import VoiceAssistant
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set mock mode for testing without making actual calls
os.environ['MOCK_MODE'] = 'true'
config.MOCK_MODE = True  # Explicitly set MOCK_MODE in config

def test_direct_hospital_call():
    """Test the direct hospital calling functionality."""
    # Initialize the Voice Assistant
    tofia = VoiceAssistant()
    
    # Display configuration
    logger.info(f"Using hospital phone number from .env: {config.HOSPITAL_PHONE_NUMBER}")
    logger.info(f"Using Tofia phone number: {config.TOFIA_PHONE_NUMBER}")
    logger.info(f"Mock mode is: {config.MOCK_MODE}")
    
    # Test patient data
    test_patient = {
        "name": "John Doe",
        "dob": "01/15/1980",
        "insurance": "BlueCross BlueShield",
        "insurance_id": "BC123456789",
        "address": "123 Main Street",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95134",
        "appointment_reason": "Annual physical checkup"
    }
    
    # Create a test call
    test_call_sid = f"test-call-{int(time.time())}"
    test_phone = "+19876543210"
    
    # Create a call record
    call_record = tofia.memory.create_call_record(test_phone, "inbound", test_call_sid)
    if call_record:
        logger.info(f"Created test call record with ID: {call_record.id}")
    else:
        logger.error("Failed to create call record")
        return
    
    # Set up active call data
    tofia.active_calls[test_call_sid] = {
        "call_sid": test_call_sid,
        "phone_number": test_phone,
        "call_record_id": call_record.id,
        "state": "patient_conversation",
        "start_time": datetime.utcnow()
    }
    
    # Call the hospital directly
    logger.info("Starting direct hospital call test")
    tofia.handle_hospital_call(test_call_sid, test_phone, test_patient)
    
    # Check if the call was successful
    logger.info("\nTest completed!")
    logger.info("Check the logs above to verify the hospital call was initiated correctly.")

if __name__ == "__main__":
    try:
        test_direct_hospital_call()
    except Exception as e:
        logger.exception(f"Error during test: {e}")
        print(f"\nTest failed with error: {e}")
