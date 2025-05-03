"""
Utility functions for the Agentic Health Assistant system.
"""
import sys
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Add parent directory to path to import from our own modules
sys.path.append('..')
from agentic.schema import ConversationMemory, UserProfile, AppointmentDetails

logger = logging.getLogger(__name__)

def create_conversation_id() -> str:
    """
    Create a unique conversation ID.
    
    Returns:
        str: A unique conversation ID
    """
    return f"conv-{uuid.uuid4().hex[:8]}"

def format_appointment_for_user(appointment: AppointmentDetails) -> str:
    """
    Format appointment details in a user-friendly way.
    
    Args:
        appointment: Appointment details
        
    Returns:
        str: Formatted appointment string
    """
    parts = []
    
    if appointment.doctor_name:
        parts.append(f"Doctor: {appointment.doctor_name}")
    
    if appointment.date and appointment.time:
        parts.append(f"Date and Time: {appointment.date} at {appointment.time}")
    elif appointment.date:
        parts.append(f"Date: {appointment.date}")
    
    if appointment.facility_name:
        location = appointment.facility_name
        if appointment.facility_address:
            location += f" ({appointment.facility_address})"
        parts.append(f"Location: {location}")
    
    if appointment.reason:
        parts.append(f"Reason: {appointment.reason}")
    
    if appointment.notes:
        parts.append(f"Notes: {appointment.notes}")
    
    return "\n".join(parts)

def extract_entities_from_text(text: str) -> Dict[str, Any]:
    """
    Extract basic entities from text for memory storage.
    
    Args:
        text: Input text
        
    Returns:
        Dict: Extracted entities
    """
    import re
    entities = {}
    
    # Simple patterns for demonstration purposes
    # In a real system, use a more robust NER system
    patterns = {
        "dates": r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2}(?:st|nd|rd|th)?\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        "times": r'\b\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)\b|\b\d{1,2}\s*(?:AM|PM|am|pm)\b',
        "phone_numbers": r'\+\d{1,3}\s?\d{3}\s?\d{3}\s?\d{4}|\(\d{3}\)\s?\d{3}-\d{4}|\b\d{3}[-. ]?\d{3}[-. ]?\d{4}\b',
        "emails": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "medications": r'\b[A-Za-z]+\s+\d+\s*(?:mg|mcg|ml)\b',
        "symptoms": r'\b(?:pain|fever|cough|headache|nausea|fatigue)\b'
    }
    
    for entity_type, pattern in patterns.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            entities[entity_type] = matches
    
    return entities

def log_conversation_step(state_before: Dict[str, Any], state_after: Dict[str, Any], agent_name: str) -> None:
    """
    Log a conversation step for debugging and analysis.
    
    Args:
        state_before: State before the agent processed
        state_after: State after the agent processed
        agent_name: Name of the agent that processed the state
    """
    # Create a compact log entry
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "agent": agent_name,
        "input_length": len(state_before.get("user_input", "")) if isinstance(state_before.get("user_input"), str) else 0,
        "output_length": len(state_after.get("response_to_user", "")) if isinstance(state_after.get("response_to_user"), str) else 0,
        "intent": state_after.get("current_intent", "unknown")
    }
    
    # Log in a structured format
    logger.info(f"AGENT_STEP: {json.dumps(log_entry)}")

def sanitize_phone_number(phone_number: str) -> str:
    """
    Sanitize a phone number for consistency.
    
    Args:
        phone_number: Input phone number
        
    Returns:
        str: Sanitized phone number
    """
    import re
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone_number)
    
    # Ensure it starts with +
    if not phone_number.startswith('+') and len(digits_only) == 10:
        # Assume US number if 10 digits and no country code
        return f"+1{digits_only}"
    elif len(digits_only) > 10 and not phone_number.startswith('+'):
        return f"+{digits_only}"
    elif phone_number.startswith('+'):
        return f"+{digits_only}"
    
    # Return original if we can't determine format
    return phone_number
