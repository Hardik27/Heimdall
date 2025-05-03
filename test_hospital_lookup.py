#!/usr/bin/env python
"""
Test script for the enhanced hospital lookup and outbound calling system.
This simulates finding hospitals by ZIP code and making outbound calls.
"""
import logging
import time
import os
from memory_module import MemoryStore
from voice_assistant import VoiceAssistant
from telephony_handler import TelephonyHandler
import config
from models import CallRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set mock mode for testing without making actual calls
os.environ['MOCK_MODE'] = 'true'

def test_hospital_lookup_and_calls():
    """Test the hospital lookup and outbound calling system."""
    # Initialize components
    memory = MemoryStore()
    tofia = VoiceAssistant()
    telephony = TelephonyHandler()
    
    # Test patient data
    test_patient = {
        "name": "Test Patient",
        "dob": "01/15/1980",
        "insurance": "BlueCross BlueShield",
        "insurance_id": "BC123456789",
        "address": "123 Main Street",
        "city": "San Jose",
        "state": "CA",
        "zip_code": "95134",  # ZIP code that matches our hospitals
        "appointment_reason": "Headache and dizziness"
    }
    
    # Find hospitals near the patient
    logger.info(f"Looking up hospitals near ZIP code {test_patient['zip_code']}")
    hospitals = memory.get_nearest_hospitals(test_patient['zip_code'])
    
    if not hospitals:
        logger.error("No hospitals found in database")
        return
    
    logger.info(f"Found {len(hospitals)} hospitals:")
    for hospital in hospitals:
        logger.info(f"  {hospital.name} - {hospital.phone_number} - ZIP: {hospital.zip_code}")
    
    # Create a test call
    test_call_sid = f"test-call-{int(time.time())}"
    test_phone = "+19876543210"
    
    # Create a call record
    call_record = memory.create_call_record(test_phone, "inbound", test_call_sid)
    if not call_record:
        logger.error("Failed to create call record")
        return
    
    logger.info(f"Created test call record with ID: {call_record.id}")
    
    # Set up active call data
    tofia.active_calls[test_call_sid] = {
        "call_sid": test_call_sid,
        "phone_number": test_phone,
        "call_record_id": call_record.id,
        "state": "patient_conversation"
    }
    
    # Call the hospital_call method
    logger.info("Starting multi-hospital call process")
    tofia.handle_hospital_call(test_call_sid, test_phone, test_patient)
    
    # Check the database for appointment records
    logger.info("\nVerifying appointment records:")
    calls = memory.get_recent_calls(test_phone, limit=3)
    
    if not calls:
        logger.error("No call records found")
        return
    
    for call in calls:
        logger.info(f"Call record ID: {call.id}")
        logger.info(f"  Call SID: {call.call_sid}")
        logger.info(f"  Call type: {call.call_type}")
        logger.info(f"  Status: {call.status}")
        
        if call.appointment_date:
            logger.info(f"  Appointment date: {call.appointment_date}")
            logger.info(f"  Appointment time: {call.appointment_time}")
            logger.info(f"  Doctor name: {call.doctor_name}")
    
    # Find all outbound calls made - use memory's session properly
    logger.info("\nOutbound calls made:")
    try:
        # Get a session directly from the memory object using its session_factory
        session = memory.session_factory()
        try:
            outbound_calls = session.query(CallRecord).filter_by(call_type="outbound").all()
            if outbound_calls:
                for call in outbound_calls:
                    logger.info(f"  Call to: {call.phone_number}")
                    logger.info(f"  Start time: {call.start_time}")
                    logger.info(f"  End time: {call.end_time}")
                    logger.info(f"  Status: {call.status}")
                    logger.info(f"  Summary: {call.summary}")
                    logger.info("  " + "-" * 30)
            else:
                logger.info("  No outbound calls found in database")
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Error querying outbound calls: {e}")
    
    logger.info("\nTest completed successfully!")

if __name__ == "__main__":
    try:
        test_hospital_lookup_and_calls()
    except Exception as e:
        logger.exception(f"Error during test: {e}")
        print(f"\nTest failed with error: {e}")
