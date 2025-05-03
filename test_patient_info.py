#!/usr/bin/env python
"""
Test script for the enhanced patient information capture functionality.
This simulates a conversation with the patient agent and verifies 
that all the information is correctly extracted and stored.
"""
import logging
import time
from conversation_agents import PatientAgent
from memory_module import MemoryStore
from voice_assistant import VoiceAssistant
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_patient_info_capture():
    """Test the enhanced patient information capture."""
    # Create a test phone number
    test_phone = "+19998887777"
    
    # Create a memory store and clear any existing record for this phone
    memory = MemoryStore()
    
    # Create a patient agent
    patient_agent = PatientAgent()
    
    # Create voice assistant
    voice_assistant = VoiceAssistant()
    
    # Create a test call record
    call_record = memory.create_call_record(test_phone, "inbound", f"test-call-{int(time.time())}")
    if not call_record:
        logger.error("Failed to create call record")
        return
    
    logger.info(f"Created test call record with ID: {call_record.id}")
    
    # Set up the active call in the voice assistant
    voice_assistant.active_calls[call_record.call_sid] = {
        "call_sid": call_record.call_sid,
        "phone_number": test_phone,
        "call_record_id": call_record.id,
        "state": "patient_conversation"
    }
    
    # Simulate a conversation with complete patient information
    test_conversation = [
        "Hi, I need to schedule a doctor's appointment.",
        "My name is John Smith.",
        "I was born on 05/15/1980.",
        "I have BlueCross BlueShield insurance.",
        "My insurance ID is BC123456789.",
        "I live at 123 Main Street, Apartment 4B.",
        "I'm in San Francisco, CA 94105.",
        "I've been having severe headaches for the past week and need to see a neurologist."
    ]
    
    # Process each message
    for message in test_conversation:
        logger.info(f"User: {message}")
        
        # Get response from patient agent
        response = patient_agent.generate_response(message)
        logger.info(f"Agent: {response}")
        
        # Save conversation history
        voice_assistant.save_conversation_history(
            call_record.call_sid, 
            "patient", 
            message, 
            response
        )
        
        # Update caller information
        voice_assistant.update_caller_info(test_phone, patient_agent.patient_info)
        
        # Show current state
        logger.info("Current patient information:")
        for key, value in patient_agent.patient_info.items():
            if value:
                logger.info(f"  {key}: {value}")
        
        logger.info("Current state:")
        for key, value in patient_agent.state.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("-" * 50)
    
    # Verify database record
    logger.info("\nVerifying database record...")
    caller = memory.get_caller(test_phone)
    
    if caller:
        logger.info(f"Caller record found: {caller.id}")
        logger.info(f"Name: {caller.name}")
        logger.info(f"Date of Birth: {caller.date_of_birth}")
        logger.info(f"Insurance Provider: {caller.insurance_provider}")
        logger.info(f"Insurance ID: {caller.insurance_id}")
        logger.info(f"Address: {caller.address}")
        logger.info(f"City: {caller.city}")
        logger.info(f"State: {caller.state}")
        logger.info(f"ZIP Code: {caller.zip_code}")
    else:
        logger.error("Caller record not found!")
    
    # Verify conversation history
    logger.info("\nVerifying conversation history...")
    calls = memory.get_recent_calls(test_phone, limit=1)
    
    if calls and calls[0]:
        call = calls[0]
        logger.info(f"Call record found: {call.id}")
        logger.info(f"Call SID: {call.call_sid}")
        logger.info(f"Summary excerpt: {call.summary[:100]}..." if call.summary else "No summary")
        
        # Check JSON conversation data
        if hasattr(call, 'conversation_json') and call.conversation_json:
            import json
            try:
                conversations = json.loads(call.conversation_json)
                logger.info(f"Found {len(conversations)} conversation entries")
            except:
                logger.error("Failed to parse conversation JSON")
    else:
        logger.error("No call records found!")

if __name__ == "__main__":
    try:
        test_patient_info_capture()
        print("\nTest completed successfully. Check the logs for details.")
    except Exception as e:
        logger.exception(f"Error during test: {e}")
        print(f"\nTest failed with error: {e}")
