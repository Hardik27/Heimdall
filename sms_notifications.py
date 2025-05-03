"""
SMS Notifications module for Tofia Voice Assistant.
Handles sending SMS confirmations using Twilio API.
"""
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import config

logger = logging.getLogger(__name__)

class SMSNotifier:
    """Handles sending SMS notifications to patients."""
    
    def __init__(self):
        """Initialize the Twilio client."""
        self.client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    
    def send_appointment_confirmation(self, phone_number, appointment_details):
        """
        Send an appointment confirmation SMS to a patient.
        
        Args:
            phone_number: The patient's phone number
            appointment_details: Dictionary containing appointment details
            
        Returns:
            bool: Success status of the SMS send operation
        """
        try:
            # Format the confirmation message using the template
            message_body = config.APPOINTMENT_CONFIRMATION_TEMPLATE.format(
                patient_name=appointment_details.get("patient_name", "Patient"),
                doctor_name=appointment_details.get("doctor_name", "your doctor"),
                appointment_date=appointment_details.get("date", "the scheduled date"),
                appointment_time=appointment_details.get("time", "the scheduled time")
            )
            
            # Send the SMS
            message = self.client.messages.create(
                body=message_body,
                from_=config.TOFIA_PHONE_NUMBER,
                to=phone_number
            )
            
            logger.info(f"SMS confirmation sent to {phone_number}, SID: {message.sid}")
            return True
            
        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            return False
