"""
Voice Assistant orchestration module for Tofia.
Ties together all components of the system.
"""
import logging
from datetime import datetime
from telephony_handler import TelephonyHandler
from conversation_agents import PatientAgent, HospitalAgent
from memory_module import MemoryStore
from sms_notifications import SMSNotifier
import config
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class VoiceAssistant:
    """Main orchestration class for the Tofia voice assistant."""
    
    def __init__(self):
        """Initialize all components of the voice assistant."""
        self.telephony = TelephonyHandler()
        self.memory = MemoryStore()
        self.sms = SMSNotifier()
        self.active_calls = {}  # Track active calls by call_sid
    
    def handle_incoming_call(self, call_data):
        """
        Handle an incoming call webhook from Vapi.
        
        Args:
            call_data: Call data from Vapi webhook
            
        Returns:
            dict: Response for Vapi
        """
        call_sid = call_data.get("call_sid")
        phone_number = call_data.get("from")
        
        logger.info(f"Incoming call from {phone_number}")
        
        # Get or create caller in database
        caller = self.memory.get_caller(phone_number)
        
        # Create call record
        call_record = self.memory.create_call_record(phone_number, "inbound", call_sid)
        
        # Store call info in active_calls
        self.active_calls[call_sid] = {
            "phone_number": phone_number,
            "caller_id": caller.id,
            "call_record_id": call_record.id if call_record else None,
            "agent": PatientAgent(),
            "start_time": datetime.utcnow()
        }
        
        # Return Vapi configuration to disable built-in assistant
        return self.telephony.handle_inbound_call(call_data)
    
    def process_patient_message(self, call_sid, message):
        """
        Process a message from a patient during an active call.
        
        Args:
            call_sid: The Vapi call identifier
            message: The patient's message
            
        Returns:
            dict: Response for Vapi
        """
        if call_sid not in self.active_calls:
            logger.error(f"Received message for unknown call: {call_sid}")
            return {"error": "Unknown call"}
        
        call_info = self.active_calls[call_sid]
        phone_number = call_info["phone_number"]
        
        # Get known information about the caller
        caller = self.memory.get_caller(phone_number)
        known_info = {
            "phone_number": phone_number,
            "name": caller.name,
            "dob": caller.date_of_birth,
            "insurance": caller.insurance_provider
        }
        
        # Generate response using patient agent
        agent = call_info["agent"]
        response = agent.generate_response(message, known_info)
        
        # Save the conversation history
        self.save_conversation_history(call_sid, "patient", message, response)
        
        # Update caller info in database if we've learned new information
        if agent.state["got_name"] and agent.patient_info["name"]:
            self.memory.update_caller(phone_number, name=agent.patient_info["name"])
        
        if agent.state["got_dob"] and agent.patient_info["dob"]:
            self.memory.update_caller(phone_number, date_of_birth=agent.patient_info["dob"])
        
        if agent.state["got_insurance"] and agent.patient_info["insurance"]:
            self.memory.update_caller(phone_number, insurance_provider=agent.patient_info["insurance"])
        
        # Check if ready to schedule with hospital
        if agent.state["ready_for_hospital_call"]:
            # End the patient call gracefully
            next_steps = "\n\nThank you for providing that information. I'll contact the hospital to schedule your appointment and send you a confirmation text message once it's confirmed. I'll be placing a real call to the hospital now."
            
            # Update call record
            if call_info["call_record_id"]:
                self.memory.update_call_record(
                    call_info["call_record_id"],
                    status="completed",
                    end_time=datetime.utcnow(),
                    summary="Patient provided info for appointment scheduling"
                )
            
            # Make a real call to the hospital - no simulation
            logger.info(f"Initiating hospital call for patient {agent.patient_info.get('name')}")
            self.handle_hospital_call(call_sid, phone_number, agent.patient_info)
            
            return {"response": response + next_steps, "end_call": True}
        
        # Update caller information in the database after each interaction
        if agent.patient_info:
            self.update_caller_info(phone_number, agent.patient_info)
            logger.info(f"Updated caller database with latest patient information")
        
        return {"response": response}
    
    def handle_hospital_call(self, call_sid, phone_number, patient_info):
        """
        Handle the outbound call to the hospital for appointment scheduling.
        
        Args:
            call_sid: The Vapi call identifier for the inbound patient call
            phone_number: The patient's phone number
            patient_info: Dictionary containing patient information
        """
        logger.info(f"Starting hospital call process for patient: {phone_number}")
        
        try:
            # Always use the hospital phone number from .env
            hospital_number = config.HOSPITAL_PHONE_NUMBER
            hospital_name = "Hospital"  # Default name
            
            logger.info(f"Calling hospital at {hospital_number}")
            
            # Update the patient about which hospital we're calling
            if call_sid in self.active_calls:
                self.telephony.send_message_to_call(
                    call_sid,
                    f"I'm calling the hospital to check for available appointments. Please hold..."
                )
            
            # Call the hospital
            appointment_details = self._call_single_hospital(
                call_sid, 
                phone_number, 
                patient_info, 
                hospital_number,
                hospital_name=hospital_name
            )
            
            # After calling the hospital, check if we got a successful booking
            if appointment_details and "appointment_confirmed" in appointment_details and appointment_details["appointment_confirmed"]:
                # Send SMS confirmation
                self.send_appointment_confirmation(phone_number, appointment_details)
                
                # Inform the patient
                self.telephony.send_message_to_call(
                    call_sid,
                    f"Great news! I've confirmed your appointment at the hospital on {appointment_details.get('date', 'the scheduled date')} at {appointment_details.get('time', 'the scheduled time')}. You'll also receive a text message confirmation. Is there anything else you need help with today?"
                )
            else:
                # No successful booking
                self.telephony.send_message_to_call(
                    call_sid,
                    "I wasn't able to schedule an appointment with the hospital at this time. You might want to try again later or call the hospital directly. Is there anything else I can help you with?"
                )
            
        except Exception as e:
            logger.error(f"Error in hospital call process: {e}")
            # Send a message to the patient about the error
            if call_sid in self.active_calls:
                self.telephony.send_message_to_call(
                    call_sid,
                    "I'm sorry, but I encountered an error while trying to schedule your appointment. Please try again later or call the hospital directly."
                )
    
    def _call_single_hospital(self, patient_call_sid, patient_phone, patient_info, hospital_number, hospital_name=None):
        """
        Make a call to a single hospital to schedule an appointment.
        
        Args:
            patient_call_sid: The Vapi call identifier for the inbound patient call
            patient_phone: The patient's phone number
            patient_info: Dictionary containing patient information
            hospital_number: The hospital's phone number
            hospital_name: The hospital's name
            
        Returns:
            dict: Appointment details if successful, None otherwise
        """
        try:
            logger.info(f"Placing outbound call to hospital at {hospital_number}")
            
            # Create context for the hospital call
            context = {
                "patient_call_sid": patient_call_sid,
                "patient_phone": patient_phone,
                "patient_info": patient_info,
                "hospital_name": hospital_name
            }
            
            # Make the real outbound call
            call_result = self.telephony.place_outbound_call(hospital_number, context)
            
            if not call_result:
                logger.error(f"Failed to place call to hospital at {hospital_number}")
                return None
                
            # Get the call SID for the hospital call
            hospital_call_sid = call_result.get("call_sid")
            
            if not hospital_call_sid:
                logger.error("No call_sid returned for hospital call")
                return None
            
            # Create hospital agent to handle the conversation
            hospital_agent = HospitalAgent(patient_info)
            
            # Store hospital call info
            self.active_calls[hospital_call_sid] = {
                "phone_number": hospital_number,
                "type": "hospital",
                "patient_call_sid": patient_call_sid,
                "patient_phone": patient_phone,
                "agent": hospital_agent,
                "start_time": datetime.utcnow()
            }
            
            # Create call record
            self.memory.create_call_record(
                patient_phone, 
                "outbound", 
                hospital_call_sid,
                call_type="hospital"
            )
            
            logger.info(f"Initiated hospital call, SID: {hospital_call_sid}")
            
            # In a real environment, the call will proceed asynchronously and the
            # process_hospital_message method will be called for each message
            # For now, just return empty details - they'll be filled in by the webhook
            return None
            
        except Exception as e:
            logger.error(f"Error making hospital call: {e}")
            return None
    
    def process_hospital_message(self, call_sid, message):
        """
        Process a message from a hospital during an active call.
        
        Args:
            call_sid: The Vapi call identifier
            message: The hospital's message
            
        Returns:
            dict: Response for Vapi
        """
        if call_sid not in self.active_calls:
            logger.error(f"Received message for unknown hospital call: {call_sid}")
            return {"error": "Unknown call"}
        
        call_info = self.active_calls[call_sid]
        
        # Generate response using hospital agent
        agent = call_info["agent"]
        response = agent.generate_response(message)
        
        # Save the conversation history
        self.save_conversation_history(call_sid, "hospital", message, response)
        
        # Check if we got appointment details
        appointment_details = agent.get_appointment_details()
        
        # If the appointment is confirmed, update the patient and end the call
        if appointment_details and appointment_details.get("appointment_confirmed"):
            # Inform the patient
            patient_call_sid = call_info.get("patient_call_sid")
            if patient_call_sid and patient_call_sid in self.active_calls:
                self.telephony.send_message_to_call(
                    patient_call_sid,
                    f"Great news! I've confirmed your appointment at {hospital_name} on {appointment_details.get('date')} at {appointment_details.get('time')}. You'll receive a text message confirmation soon."
                )
            
            # Send SMS confirmation
            patient_phone = call_info.get("patient_phone")
            if patient_phone:
                self.send_appointment_confirmation(patient_phone, appointment_details)
            
            # Thank the receptionist and end the call
            return {"response": response, "end_call": True}
        
        return {"response": response}
    
    def handle_call_status_update(self, status_data):
        """
        Handle call status update from Vapi.
        
        Args:
            status_data: Status data from Vapi
        """
        call_sid = status_data.get("call_sid")
        status = status_data.get("status")
        
        logger.info(f"Call status update for {call_sid}: {status}")
        
        if status == "completed" and call_sid in self.active_calls:
            call_info = self.active_calls[call_sid]
            
            # Update call record in database
            call_record_id = call_info.get("call_record_id")
            if call_record_id:
                self.memory.update_call_record(
                    call_record_id,
                    status="completed",
                    end_time=datetime.utcnow()
                )
            
            # Clean up active calls
            del self.active_calls[call_sid]
            logger.info(f"Removed call {call_sid} from active calls")
    
    def save_conversation_history(self, call_sid, role, message, response):
        """
        Save conversation history to the database.
        
        Args:
            call_sid: The Vapi call identifier
            role: The role of the speaker ("patient" or "hospital")
            message: The message
            response: The response
        """
        if call_sid not in self.active_calls:
            logger.error(f"Cannot save conversation history for unknown call: {call_sid}")
            return
        
        call_info = self.active_calls[call_sid]
        call_record_id = call_info.get("call_record_id")
        
        if not call_record_id:
            logger.error(f"No call record ID for call {call_sid}")
            return
        
        # Get existing conversation history
        call_record = self.memory.get_call_record(call_record_id)
        if not call_record:
            logger.error(f"Call record not found for ID {call_record_id}")
            return
        
        # Parse existing history or create new
        try:
            existing_history = json.loads(call_record.conversation_json) if call_record.conversation_json else []
        except:
            existing_history = []
        
        # Add new messages
        existing_history.append({
            "role": role,
            "text": message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        existing_history.append({
            "role": "tofia",
            "text": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update the record
        self.memory.update_call_record(
            call_record_id,
            conversation_json=json.dumps(existing_history)
        )
    
    def update_caller_info(self, phone_number, patient_info):
        """
        Update caller information in the database.
        
        Args:
            phone_number: The caller's phone number
            patient_info: Dictionary containing patient information
        """
        update_dict = {}
        
        if patient_info.get("name"):
            update_dict["name"] = patient_info["name"]
        
        if patient_info.get("dob"):
            update_dict["date_of_birth"] = patient_info["dob"]
        
        if patient_info.get("insurance"):
            update_dict["insurance_provider"] = patient_info["insurance"]
        
        if patient_info.get("insurance_id"):
            update_dict["insurance_id"] = patient_info["insurance_id"]
        
        if patient_info.get("address"):
            update_dict["address"] = patient_info["address"]
        
        if patient_info.get("city"):
            update_dict["city"] = patient_info["city"]
        
        if patient_info.get("state"):
            update_dict["state"] = patient_info["state"]
        
        if patient_info.get("zip_code"):
            update_dict["zip_code"] = patient_info["zip_code"]
        
        if update_dict:
            self.memory.update_caller(phone_number, **update_dict)
    
    def send_appointment_confirmation(self, phone_number, appointment_details):
        """
        Send appointment confirmation via SMS.
        
        Args:
            phone_number: The patient's phone number
            appointment_details: Dictionary containing appointment details
        """
        if not appointment_details:
            logger.error("Cannot send confirmation - no appointment details")
            return
        
        caller = self.memory.get_caller(phone_number)
        if not caller:
            logger.error(f"Cannot send confirmation - caller not found for {phone_number}")
            return
        
        # Format the appointment confirmation message
        message = config.APPOINTMENT_CONFIRMATION_TEMPLATE.format(
            patient_name=caller.name or "Patient",
            doctor_name=appointment_details.get("doctor", "your doctor"),
            hospital_name=appointment_details.get("hospital_name", "the hospital"),
            appointment_date=appointment_details.get("date", "the scheduled date"),
            appointment_time=appointment_details.get("time", "the scheduled time")
        )
        
        # Send the SMS
        self.sms.send_sms(phone_number, message)
        logger.info(f"Sent appointment confirmation SMS to {phone_number}")
