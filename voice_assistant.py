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
            next_steps = "\n\nThank you for providing that information. I'll contact the hospital to schedule your appointment and send you a confirmation text message once it's confirmed."
            
            # Update call record
            if call_info["call_record_id"]:
                self.memory.update_call_record(
                    call_info["call_record_id"],
                    status="completed",
                    end_time=datetime.utcnow(),
                    summary="Patient provided info for appointment scheduling"
                )
            
            # Queue hospital call (would happen after this call ends in production)
            # For now, we'll simulate it
            self._schedule_hospital_appointment(phone_number, agent.patient_info)
            
            return {"response": response + next_steps, "end_call": True}
        
        return {"response": response}
    
    def _schedule_hospital_appointment(self, phone_number, patient_info):
        """
        Schedule an appointment with the hospital.
        
        Args:
            phone_number: The patient's phone number
            patient_info: Information about the patient
        """
        logger.info(f"Scheduling hospital appointment for {patient_info.get('name', 'patient')}")
        
        # In a production environment, we would place an outbound call to the hospital
        # For demonstration purposes, we'll simulate the conversation
        
        # Create outbound call record
        call_record = self.memory.create_call_record(phone_number, "outbound")
        
        # Simulate hospital conversation
        appointment_details = self.telephony.simulate_hospital_conversation(patient_info)
        
        # Update call record with appointment details
        if call_record:
            self.memory.update_call_record(
                call_record.id,
                status="completed",
                end_time=datetime.utcnow(),
                summary="Appointment scheduled",
                appointment_date=appointment_details.get("date"),
                appointment_time=appointment_details.get("time"),
                doctor_name=appointment_details.get("doctor_name")
            )
        
        # Send SMS confirmation to patient
        self.send_appointment_confirmation(phone_number, appointment_details)
    
    def place_hospital_call(self, phone_number, patient_info):
        """
        Place an outbound call to the hospital.
        
        Args:
            phone_number: The patient's phone number
            patient_info: Information about the patient
            
        Returns:
            str: Call SID if successful, None otherwise
        """
        # Create outbound call record
        call_record = self.memory.create_call_record(phone_number, "outbound")
        
        # Place the call
        call_sid = self.telephony.place_outbound_call(config.HOSPITAL_PHONE_NUMBER, patient_info)
        
        if call_sid and call_record:
            # Update call record with call_sid
            self.memory.update_call_record(call_record.id, call_sid=call_sid)
            
            # Store call info in active_calls
            self.active_calls[call_sid] = {
                "phone_number": phone_number,
                "call_record_id": call_record.id,
                "agent": HospitalAgent(patient_info),
                "start_time": datetime.utcnow()
            }
        
        return call_sid
    
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
            logger.error(f"Received message for unknown call: {call_sid}")
            return {"error": "Unknown call"}
        
        call_info = self.active_calls[call_sid]
        
        # Generate response using hospital agent
        agent = call_info["agent"]
        response = agent.generate_response(message)
        
        # Check if appointment is confirmed
        if agent.state["appointment_confirmed"]:
            # Get appointment details
            appointment_details = agent.get_appointment_details()
            appointment_details["patient_name"] = agent.patient_info.get("name", "Patient")
            
            # Update call record with appointment details
            if call_info["call_record_id"]:
                self.memory.update_call_record(
                    call_info["call_record_id"],
                    status="completed",
                    end_time=datetime.utcnow(),
                    summary="Appointment scheduled",
                    appointment_date=appointment_details.get("date"),
                    appointment_time=appointment_details.get("time"),
                    doctor_name=appointment_details.get("doctor_name")
                )
            
            # Send SMS confirmation
            self.send_appointment_confirmation(call_info["phone_number"], appointment_details)
            
            # End call gracefully
            next_steps = "\n\nThank you for your help. I've confirmed the appointment details. Have a great day!"
            return {"response": response + next_steps, "end_call": True}
        
        return {"response": response}
    
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
    
    def send_appointment_confirmation(self, phone_number, appointment_details):
        """
        Send an appointment confirmation SMS to a patient.
        
        Args:
            phone_number: The patient's phone number
            appointment_details: Dictionary containing appointment details
            
        Returns:
            bool: Success status of the SMS send operation
        """
        logger.info(f"Sending appointment confirmation to {phone_number}")
        
        # Send the SMS
        success = self.sms.send_appointment_confirmation(phone_number, appointment_details)
        
        if success:
            logger.info("SMS confirmation sent successfully")
        else:
            logger.warning("Failed to send SMS confirmation")
        
        return success
