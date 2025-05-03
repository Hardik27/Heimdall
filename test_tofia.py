"""
Test script for Tofia Voice Assistant.
Simulates a complete patient call flow without needing webhook endpoints.
"""
import logging
import sys
from datetime import datetime
from models import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def simulate_patient_call():
    """Simulate a complete patient call flow."""
    
    logger.info("SIMULATION: Initializing database")
    # Initialize database
    init_db()
    
    logger.info("SIMULATION: Simulating entire flow without actual API calls")
    logger.info("Patient call → Information collection → Hospital scheduling → SMS confirmation")
    
    # Demonstrate workflow with simulated data
    patient_info = {
        "name": "John Smith",
        "dob": "January 15, 1980",
        "insurance": "Blue Cross Blue Shield",
        "symptoms": "Severe headaches for the past week",
        "preferred_timeframe": "Next week"
    }
    
    appointment_details = {
        "patient_name": patient_info["name"],
        "date": "tomorrow",
        "time": "2:30 PM",
        "doctor_name": "Dr. Smith"
    }
    
    # Print workflow demonstration
    logger.info("=== Tofia Voice Assistant Workflow Demonstration ===")
    logger.info("1. Incoming call from patient")
    logger.info(f"2. Patient identification: {patient_info['name']}")
    logger.info(f"3. Patient provided information: DOB: {patient_info['dob']}, Insurance: {patient_info['insurance']}")
    logger.info(f"4. Patient described symptoms: {patient_info['symptoms']}")
    logger.info(f"5. Patient preferred timeframe: {patient_info['preferred_timeframe']}")
    logger.info("6. Patient call completed and information stored in database")
    logger.info("7. Outbound call to hospital placed")
    logger.info(f"8. Appointment scheduled: {appointment_details['date']} at {appointment_details['time']} with {appointment_details['doctor_name']}")
    logger.info("9. SMS confirmation sent to patient")
    logger.info("10. Appointment details saved to database")
    logger.info("=== Workflow completed successfully ===")
    
    logger.info("\nNOTE: This is a simulated demonstration. To run the full application:")
    logger.info("1. Configure your API keys in the .env file")
    logger.info("2. Run 'uvicorn app:app --reload' to start the FastAPI server")
    logger.info("3. Configure Vapi to send webhooks to your endpoints")
    
if __name__ == "__main__":
    simulate_patient_call()
