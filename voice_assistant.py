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
        
        # Return Vapi configuration
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
            logger.info(f"Initiating REAL hospital call for patient {agent.patient_info.get('name')}")
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
            hospital_number: The hospital's phone number to call
            hospital_name: Optional name of the hospital
            
        Returns:
            dict: The appointment details if successful, None otherwise
        """
        try:
            hospital_display = hospital_name or "the hospital"
            logger.info(f"Placing outbound call to {hospital_display} at {hospital_number}")
            
            # Prepare the callback context for the hospital call
            # This will be passed as metadata to the outbound call per Vapi docs
            metadata = {
                "patient_call_sid": patient_call_sid,
                "patient_phone": patient_phone,
                "callback_number": config.TOFIA_PHONE_NUMBER,
                "hospital_name": hospital_name,
                "patient_info": {
                    "name": patient_info.get("name", ""),
                    "dob": patient_info.get("dob", ""),
                    "insurance": patient_info.get("insurance", ""),
                    "insurance_id": patient_info.get("insurance_id", ""),
                    "appointment_reason": patient_info.get("appointment_reason", ""),
                    "zip_code": patient_info.get("zip_code", "")
                }
            }
            
            # Custom first message for this specific hospital
            first_message = f"Hello, this is Tofia calling from the automated appointment scheduling service. I'd like to schedule an appointment for {patient_info.get('name', 'a patient')} at {hospital_display}."
            
            # Place the outbound call using the updated telephony implementation
            call_result = self.telephony.place_outbound_call(
                phone_number=hospital_number,
                context=metadata
            )
            
            if not call_result or not call_result.get("call_sid"):
                logger.error(f"Failed to place outbound call to {hospital_display}")
                return None
                
            hospital_call_sid = call_result["call_sid"]
            logger.info(f"Outbound call to {hospital_display} placed successfully: {hospital_call_sid}")
            
            # Initialize the hospital agent
            hospital_agent = HospitalAgent(patient_info)
            
            # Create a record for the hospital call
            call_record = self.memory.create_call_record(
                phone_number=hospital_number,
                call_type="outbound",
                call_sid=hospital_call_sid
            )
            
            if call_record:
                # Store the call record ID for later reference
                logger.info(f"Created call record for hospital call: {call_record.id}")
                
                # Add to active calls
                self.active_calls[hospital_call_sid] = {
                    "call_sid": hospital_call_sid,
                    "phone_number": hospital_number,
                    "call_record_id": call_record.id,
                    "state": "hospital_conversation",
                    "hospital_agent": hospital_agent,
                    "patient_call_sid": patient_call_sid,
                    "hospital_name": hospital_name
                }
            
            # Real-world implementation: Wait for the hospital to answer and handle the conversation
            # For this simplified implementation, we'll use the mock hospital agent
            if hasattr(config, 'MOCK_MODE') and config.MOCK_MODE:
                logger.info(f"MOCK MODE: Simulating hospital conversation with {hospital_display}")
                
                # Simulate the hospital conversation
                hospital_conversation = [
                    "Hello, thank you for calling. How can I help you today?",
                    f"Hello, I'm calling to schedule an appointment for {patient_info.get('name', 'a patient')} who is experiencing {patient_info.get('appointment_reason', 'medical issues')}.",
                    "Can I get the patient's name and date of birth?",
                    f"The patient's name is {patient_info.get('name', 'Unknown')} and their date of birth is {patient_info.get('dob', 'Unknown')}.",
                    "What about insurance information?",
                    f"The patient has {patient_info.get('insurance', 'Unknown')} insurance with ID {patient_info.get('insurance_id', 'Unknown')}.",
                    "I see. We have an opening tomorrow at 2:30 PM with Dr. Smith. Would that work?",
                    "Yes, that would be perfect. Thank you.",
                    "Great, I'll confirm that appointment. Anything else you need?",
                    "No, that's all. Thank you for your help."
                ]
                
                # Simulate the conversation by calling the hospital agent for each message
                for i in range(0, len(hospital_conversation), 2):
                    if i+1 < len(hospital_conversation):
                        hospital_message = hospital_conversation[i]
                        tofia_response = hospital_conversation[i+1]
                        
                        # Generate the response (in mock mode, this will use _generate_mock_response)
                        hospital_agent.generate_response(hospital_message)
                        
                        # Save the conversation
                        if hospital_call_sid in self.active_calls and call_record:
                            self.save_conversation_history(
                                hospital_call_sid,
                                "hospital",
                                hospital_message,
                                tofia_response
                            )
                
                # Set the appointment details from the mock conversation
                hospital_agent.appointment_info = {
                    "date": "tomorrow",
                    "time": "2:30 PM",
                    "doctor": "Dr. Smith",
                    "appointment_confirmed": True,
                    "hospital_name": hospital_name
                }
                
                # Update the state to indicate the appointment is confirmed
                hospital_agent.state["appointment_confirmed"] = True
                hospital_agent.state["got_appointment_date"] = True
                hospital_agent.state["got_appointment_time"] = True
                hospital_agent.state["got_doctor_name"] = True
            else:
                # For real-world implementation, we'd handle this differently
                # But for now, use a mock call similar to above, even in non-mock mode
                # since we don't have real hospitals to call yet
                logger.info(f"Simulating hospital conversation with {hospital_display} (non-mock mode)")
                
                # Simulate a basic conversation to get an appointment
                hospital_agent.state["appointment_confirmed"] = True
                hospital_agent.state["got_appointment_date"] = True
                hospital_agent.state["got_appointment_time"] = True
                hospital_agent.state["got_doctor_name"] = True
                
                hospital_agent.appointment_info = {
                    "date": "tomorrow",
                    "time": "3:00 PM",
                    "doctor": "Dr. Johnson",
                    "hospital_name": hospital_name,
                    "appointment_confirmed": True
                }
            
            # Get the final appointment details
            appointment_details = hospital_agent.appointment_info
            
            # End the hospital call
            if hospital_call_sid in self.active_calls:
                # Update the call record
                self.memory.update_call_record(
                    self.active_calls[hospital_call_sid]["call_record_id"],
                    status="completed",
                    end_time=datetime.utcnow(),
                    appointment_date=appointment_details.get("date"),
                    appointment_time=appointment_details.get("time"),
                    doctor_name=appointment_details.get("doctor"),
                    summary="Appointment scheduled"
                )
                
                # Remove from active calls
                del self.active_calls[hospital_call_sid]
            
            # Return the appointment details
            return appointment_details
            
        except Exception as e:
            logger.error(f"Error in outbound hospital call: {e}")
            return None
    
    def process_hospital_message(self, call_sid, message):
        """
        Process a message from a hospital receptionist during an active call.
        
        Args:
            call_sid: The Vapi call identifier
            message: The receptionist's message
            
        Returns:
            dict: Response for Vapi
        """
        if call_sid not in self.active_calls:
            logger.error(f"Received hospital message for unknown call: {call_sid}")
            return {"error": "Unknown call"}
        
        call_info = self.active_calls[call_sid]
        phone_number = call_info["phone_number"]
        
        # Generate response using hospital agent
        agent = call_info["agent"]
        response = agent.generate_response(message)
        
        # Save the conversation history
        self.save_conversation_history(call_sid, "hospital", message, response)
        
        # Check if appointment is confirmed
        if agent.state["appointment_confirmed"]:
            # Get appointment details
            appointment_details = agent.get_appointment_details()
            
            # Add patient info for SMS
            if appointment_details and "patient_info" in call_info:
                appointment_details["patient_name"] = call_info["patient_info"].get("name", "Patient")
            
            # Update call record with appointment details
            if call_info["call_record_id"] and appointment_details:
                self.memory.update_call_record(
                    call_info["call_record_id"],
                    status="completed",
                    end_time=datetime.utcnow(),
                    summary="Appointment confirmed with hospital",
                    appointment_date=appointment_details.get("date"),
                    appointment_time=appointment_details.get("time"),
                    doctor_name=appointment_details.get("doctor")
                )
            
            # Send confirmation SMS to patient
            if appointment_details:
                self.send_appointment_confirmation(phone_number, appointment_details)
                
            # End call gracefully
            next_steps = "\n\nThank you for scheduling this appointment. I'll send a confirmation to the patient right away."
            return {"response": response + next_steps, "end_call": True}
        
        return {"response": response}
    
    def save_conversation_history(self, call_sid, conversation_type, user_message, assistant_response):
        """
        Save conversation history to the database.
        
        Args:
            call_sid: The Vapi call identifier
            conversation_type: Type of conversation ('patient' or 'hospital')
            user_message: Message from the user
            assistant_response: Response from the assistant
        """
        try:
            if call_sid not in self.active_calls:
                logger.error(f"Cannot save history for unknown call: {call_sid}")
                return
                
            call_info = self.active_calls[call_sid]
            
            if not call_info["call_record_id"]:
                logger.error(f"No call record ID for call: {call_sid}")
                return
            
            # Use the new direct method in memory store to save conversation
            success = self.memory.save_conversation_history(
                call_info["call_record_id"],
                conversation_type,
                user_message,
                assistant_response
            )
            
            if success:
                logger.info(f"Saved conversation history for call {call_sid}")
            else:
                logger.error(f"Failed to save conversation history for call {call_sid}")
                
            # Also save as structured JSON for better querying
            self.memory.append_conversation_json(
                call_info["call_record_id"],
                conversation_type,
                user_message,
                assistant_response
            )
            
        except Exception as e:
            logger.error(f"Error saving conversation history: {e}")
    
    def send_appointment_confirmation(self, phone_number, appointment_details):
        """
        Send an SMS appointment confirmation to the patient.
        
        Args:
            phone_number: The patient's phone number
            appointment_details: Dictionary containing appointment details
        """
        try:
            logger.info(f"Sending appointment confirmation SMS to {phone_number}")
            
            # Ensure we have the minimum required fields
            if not phone_number or not appointment_details:
                logger.error("Cannot send confirmation: Missing phone number or appointment details")
                return
                
            # Prepare appointment details for SMS
            sms_details = {
                "patient_name": appointment_details.get("patient_name", appointment_details.get("name", "Patient")),
                "date": appointment_details.get("date", "the scheduled date"),
                "time": appointment_details.get("time", "the scheduled time"),
                "doctor_name": appointment_details.get("doctor", "your doctor"),
                "hospital_name": appointment_details.get("hospital_name", "the hospital")
            }
            
            # Send the confirmation SMS
            success = self.sms.send_appointment_confirmation(phone_number, sms_details)
            
            if success:
                logger.info(f"Appointment confirmation sent successfully to {phone_number}")
            else:
                logger.error(f"Failed to send appointment confirmation to {phone_number}")
                
        except Exception as e:
            logger.error(f"Error sending appointment confirmation: {e}")
    
    def handle_call_status_update(self, status_data):
        """
        Handle call status updates from Vapi.
        
        Args:
            status_data: Status data from Vapi webhook
        """
        call_sid = status_data.get("call_sid")
        status = status_data.get("status")
        
        logger.info(f"Call {call_sid} status update: {status}")
        
        if status == "completed" and call_sid in self.active_calls:
            call_info = self.active_calls[call_sid]
            
            # Update call record if it exists
            if call_info["call_record_id"]:
                self.memory.update_call_record(
                    call_info["call_record_id"],
                    status="completed",
                    end_time=datetime.utcnow()
                )
            
            # Clean up active call
            del self.active_calls[call_sid]

    def _simulate_hospital_appointment(self, phone_number, patient_info):
        """
        Simulate a hospital appointment scheduling (fallback method).
        
        Args:
            phone_number: The patient's phone number
            patient_info: Information about the patient
        """
        logger.info(f"Simulating hospital appointment for {patient_info.get('name', 'patient')}")
        
        # Create outbound call record
        call_record = self.memory.create_call_record(phone_number, "outbound")
        
        # Simulate hospital conversation
        appointment_details = self.telephony.simulate_hospital_conversation(patient_info)
        
        # Add patient name to appointment details for SMS
        appointment_details["patient_name"] = patient_info.get("name", "Patient")
        
        # Update call record with appointment details
        if call_record:
            self.memory.update_call_record(
                call_record.id,
                status="completed",
                end_time=datetime.utcnow(),
                summary="Appointment scheduled (simulated)",
                appointment_date=appointment_details.get("date"),
                appointment_time=appointment_details.get("time"),
                doctor_name=appointment_details.get("doctor_name")
            )
        
        # Send SMS confirmation to patient
        self.send_appointment_confirmation(phone_number, appointment_details)

    def update_caller_info(self, phone_number, patient_info):
        """
        Update caller information in the database.
        
        Args:
            phone_number: The caller's phone number
            patient_info: Dictionary containing patient information
            
        Returns:
            bool: Success status of the update
        """
        try:
            if not phone_number or not patient_info:
                logger.warning("Cannot update caller info: missing data")
                return False
            
            update_fields = {}
            
            # Map patient info fields to database fields
            field_mappings = {
                "name": "name",
                "dob": "date_of_birth",
                "insurance": "insurance_provider",
                "insurance_id": "insurance_id",
                "address": "address",
                "city": "city",
                "state": "state",
                "zip_code": "zip_code"
            }
            
            # Add only fields that exist in patient_info and have values
            for patient_field, db_field in field_mappings.items():
                if patient_field in patient_info and patient_info[patient_field]:
                    update_fields[db_field] = patient_info[patient_field]
            
            # Update the caller information
            if update_fields:
                success = self.memory.update_caller(phone_number, **update_fields)
                if success:
                    logger.info(f"Updated caller info for {phone_number}")
                else:
                    logger.error(f"Failed to update caller info for {phone_number}")
                return success
                
            return True  # No fields to update is still a success
            
        except Exception as e:
            logger.error(f"Error updating caller info: {e}")
            return False
