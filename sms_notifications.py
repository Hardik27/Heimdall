"""
SMS Notifications module for Tofia Voice Assistant.
Handles sending SMS confirmations using Twilio API.
"""
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import config
import time
import requests

logger = logging.getLogger(__name__)

class SMSNotifier:
    """Handles sending SMS notifications to patients."""
    
    def __init__(self):
        """Initialize the Twilio client."""
        self.client = None
        self.max_retries = 3
        
        # Don't create Twilio client if we're in mock mode
        if not hasattr(config, 'MOCK_MODE') or not config.MOCK_MODE:
            try:
                self.client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
                logger.info("Twilio client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing Twilio client: {e}")
                self.client = None
    
    def send_appointment_confirmation(self, phone_number, appointment_details):
        """
        Send an appointment confirmation SMS to a patient.
        
        Args:
            phone_number: The patient's phone number
            appointment_details: Dictionary containing appointment details
            
        Returns:
            bool: Success status of the SMS send operation
        """
        # Validate inputs
        if not phone_number:
            logger.error("Cannot send SMS: phone_number is required")
            return False
        
        if not appointment_details:
            logger.error("Cannot send SMS: appointment_details is required")
            return False
        
        # HIPAA compliance: Ensure we don't include any PHI in logs
        safe_details = appointment_details.copy()
        if "patient_name" in safe_details:
            safe_details["patient_name"] = "REDACTED"
        
        logger.info(f"Preparing to send appointment confirmation to {phone_number} with details: {safe_details}")
        
        # In mock mode, just simulate sending
        if hasattr(config, 'MOCK_MODE') and config.MOCK_MODE:
            logger.info(f"MOCK MODE: Simulating SMS to {phone_number}")
            # Simulate delay
            time.sleep(0.5)
            return True
            
        # Format the confirmation message using the template
        try:
            message_body = config.APPOINTMENT_CONFIRMATION_TEMPLATE.format(
                patient_name=appointment_details.get("patient_name", "Patient"),
                doctor_name=appointment_details.get("doctor_name", "your doctor"),
                hospital_name=appointment_details.get("hospital_name", "the hospital"),
                appointment_date=appointment_details.get("date", "the scheduled date"),
                appointment_time=appointment_details.get("time", "the scheduled time")
            )
            
            # If Twilio client failed to initialize, try direct API as fallback
            if self.client is None:
                return self._send_sms_direct_api(phone_number, message_body)
                
            # Send the SMS with retries
            return self._send_sms_with_retry(phone_number, message_body)
                
        except Exception as e:
            logger.error(f"Error preparing or sending SMS: {e}")
            return False
        
    def _send_sms_with_retry(self, phone_number, message_body):
        """
        Send an SMS with retries.
        
        Args:
            phone_number: The recipient's phone number
            message_body: The message content
            
        Returns:
            bool: Success status
        """
        retries = 0
        last_error = None
        
        while retries < self.max_retries:
            try:
                message = self.client.messages.create(
                    body=message_body,
                    from_=config.TOFIA_PHONE_NUMBER,
                    to=phone_number
                )
                
                logger.info(f"SMS confirmation sent to {phone_number}, SID: {message.sid}")
                return True
                
            except TwilioRestException as e:
                last_error = e
                logger.warning(f"Twilio error on attempt {retries+1}: {e}")
                
                # Don't retry if it's an authentication error or invalid number
                if e.code in [20003, 21211, 21214]:
                    break
                    
                retries += 1
                if retries < self.max_retries:
                    time.sleep(1 * retries)  # Exponential backoff
                    
            except Exception as e:
                last_error = e
                logger.warning(f"Error on attempt {retries+1}: {e}")
                retries += 1
                if retries < self.max_retries:
                    time.sleep(1 * retries)
        
        logger.error(f"Failed to send SMS after {self.max_retries} attempts: {last_error}")
        
        # Try direct API as fallback
        return self._send_sms_direct_api(phone_number, message_body)
    
    def _send_sms_direct_api(self, phone_number, message_body):
        """
        Send SMS using direct Twilio API call as fallback.
        
        Args:
            phone_number: The recipient's phone number
            message_body: The message content
            
        Returns:
            bool: Success status
        """
        try:
            logger.info("Attempting to send SMS using direct API call")
            
            url = f"https://api.twilio.com/2010-04-01/Accounts/{config.TWILIO_ACCOUNT_SID}/Messages.json"
            auth = (config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
            data = {
                "To": phone_number,
                "From": config.TOFIA_PHONE_NUMBER,
                "Body": message_body
            }
            
            response = requests.post(url, data=data, auth=auth)
            
            if response.status_code == 201:
                response_data = response.json()
                logger.info(f"SMS sent via direct API, SID: {response_data.get('sid')}")
                return True
            else:
                logger.error(f"Direct API SMS failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error with direct API SMS: {e}")
            return False
