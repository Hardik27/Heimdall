#!/usr/bin/env python
"""
Simple test script for the enhanced patient information capture functionality.
"""
import logging
import os
import json
import sqlite3
from memory_module import MemoryStore
import time

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    # Connect directly to the database
    conn = sqlite3.connect('tofia.db')
    cursor = conn.cursor()
    
    # Create a test caller with complete information
    test_phone = "+19876543210"
    test_time = int(time.time())
    test_name = f"Test Patient {test_time}"
    
    # Check if caller already exists
    cursor.execute("SELECT id FROM callers WHERE phone_number = ?", (test_phone,))
    caller = cursor.fetchone()
    
    if caller:
        caller_id = caller[0]
        logger.info(f"Using existing caller with ID: {caller_id}")
        
        # Update caller with detailed information
        cursor.execute("""
            UPDATE callers SET 
                name = ?,
                date_of_birth = ?,
                insurance_provider = ?,
                insurance_id = ?,
                address = ?,
                city = ?,
                state = ?,
                zip_code = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            test_name,
            "1985-04-15",
            "BlueCross BlueShield",
            "BC123456789",
            "456 Oak Street, Apt 7B",
            "San Francisco",
            "CA",
            "94107",
            caller_id
        ))
        logger.info("Updated existing caller record with complete information")
    else:
        # Insert new caller with complete information
        cursor.execute("""
            INSERT INTO callers (
                phone_number, name, date_of_birth, insurance_provider, 
                insurance_id, address, city, state, zip_code,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            test_phone,
            test_name,
            "1985-04-15",
            "BlueCross BlueShield",
            "BC123456789",
            "456 Oak Street, Apt 7B",
            "San Francisco",
            "CA",
            "94107"
        ))
        caller_id = cursor.lastrowid
        logger.info(f"Created new caller with ID: {caller_id}")
    
    # Create a test call record
    call_sid = f"test-enhanced-{test_time}"
    cursor.execute("""
        INSERT INTO call_records (
            caller_id, call_type, call_sid, start_time, status
        ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
    """, (
        caller_id,
        "inbound",
        call_sid,
        "in_progress"
    ))
    call_id = cursor.lastrowid
    logger.info(f"Created call record with ID: {call_id}")
    
    # Create test conversation
    test_conversation = [
        ("I need to schedule an appointment with a doctor", "I can help you schedule an appointment. Can I get your name please?"),
        (f"My name is {test_name}", f"Thank you, {test_name}. What is your date of birth?"),
        ("I was born on April 15, 1985", "Thank you. And what insurance provider do you have?"),
        ("I have BlueCross BlueShield, policy number BC123456789", "Got it. What's your address?"),
        ("I live at 456 Oak Street, Apt 7B, San Francisco, CA 94107", "Thank you for providing your address. What's the reason for your appointment?"),
        ("I've been having severe headaches and dizziness for the past week", "I'm sorry to hear that. I'll note that down. Let me schedule an appointment for you.")
    ]
    
    # Create conversation summary
    summary = ""
    conversation_json = []
    
    for i, (user_msg, assistant_msg) in enumerate(test_conversation):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(test_time + i*60))
        summary += f"\n[{timestamp} - PATIENT]\nUser: {user_msg}\nAssistant: {assistant_msg}"
        
        conversation_json.append({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(test_time + i*60)),
            "type": "patient",
            "user_message": user_msg,
            "assistant_response": assistant_msg
        })
    
    # Update call record with conversation
    cursor.execute("""
        UPDATE call_records SET 
            summary = ?,
            conversation_json = ?
        WHERE id = ?
    """, (
        summary,
        json.dumps(conversation_json),
        call_id
    ))
    
    # Commit changes
    conn.commit()
    logger.info("Saved conversation history")
    
    # Verify the data
    logger.info("\nVerifying caller information:")
    cursor.execute("""
        SELECT phone_number, name, date_of_birth, insurance_provider, insurance_id, 
               address, city, state, zip_code
        FROM callers WHERE id = ?
    """, (caller_id,))
    caller_info = cursor.fetchone()
    
    if caller_info:
        fields = ["Phone", "Name", "DOB", "Insurance", "Insurance ID", "Address", "City", "State", "ZIP"]
        for i, field in enumerate(fields):
            logger.info(f"{field}: {caller_info[i]}")
    
    logger.info("\nVerifying conversation history:")
    cursor.execute("SELECT summary, conversation_json FROM call_records WHERE id = ?", (call_id,))
    call_data = cursor.fetchone()
    
    if call_data:
        summary, convo_json = call_data
        logger.info("Summary excerpt:")
        logger.info(summary[:200] + "..." if len(summary) > 200 else summary)
        
        logger.info("\nJSON conversation data:")
        parsed_json = json.loads(convo_json)
        logger.info(f"Found {len(parsed_json)} conversation entries")
        
        # Show first entry
        if parsed_json:
            entry = parsed_json[0]
            logger.info(f"First entry:")
            logger.info(f"  Timestamp: {entry['timestamp']}")
            logger.info(f"  Type: {entry['type']}")
            logger.info(f"  User: {entry['user_message']}")
            logger.info(f"  Assistant: {entry['assistant_response']}")
    
    # Close connection
    conn.close()
    logger.info("\nTest completed successfully!")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Error: {e}")
