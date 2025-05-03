"""
Conversation Agents module for Tofia Voice Assistant.
Implements PatientAgent and HospitalAgent for handling conversations with patients and hospital staff.
"""
import logging
import openai
import json
import config
import prompts
import re

logger = logging.getLogger(__name__)

class ConversationAgent:
    """Base class for conversation agents."""
    
    def __init__(self, system_prompt):
        """
        Initialize the conversation agent.
        
        Args:
            system_prompt: System message for the GPT model
        """
        self.system_prompt = system_prompt
        self.conversation_history = []
        self.state = {}
        
        # Configure OpenAI API key
        openai.api_key = config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    
    def add_message(self, role, content):
        """
        Add a message to the conversation history.
        
        Args:
            role: The role ("system", "user", "assistant")
            content: The message content
        """
        self.conversation_history.append({"role": role, "content": content})
    
    def _prepare_messages(self):
        """
        Prepare the messages for the OpenAI API call.
        
        Returns:
            list: List of message dictionaries
        """
        # Start with the system message
        messages = [{"role": "system", "content": self.system_prompt}]
        
        # Add conversation history
        messages.extend(self.conversation_history)
        
        return messages
    
    def generate_response(self, user_message):
        """
        Generate a response using the GPT model.
        
        Args:
            user_message: The user's message to respond to
            
        Returns:
            str: The generated response
        """
        messages = self._prepare_messages()
        
        # Add the user message to history
        self.add_message("user", user_message)
        
        try:
            # Use the OpenAI client API
            response = self.client.chat.completions.create(
                model=config.GPT_MODEL,
                messages=messages,
                max_tokens=config.MAX_TOKENS,
                temperature=config.TEMPERATURE
            )
            
            assistant_response = response.choices[0].message.content
            
            # Add the response to history
            self.add_message("assistant", assistant_response)
            
            # Update state based on response
            self._update_state(assistant_response)
            
            return assistant_response
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _update_state(self, response):
        """
        Update the state based on the current response.
        To be implemented by subclasses.
        
        Args:
            response: The assistant's response
        """
        pass
    
    def get_conversation_summary(self):
        """
        Get a summary of the conversation.
        
        Returns:
            str: Summary of the conversation
        """
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
    
    def get_state(self):
        """
        Get the current state of the conversation.
        
        Returns:
            dict: The current state
        """
        return self.state


class PatientAgent(ConversationAgent):
    """Agent for handling conversations with patients."""
    
    def __init__(self):
        """Initialize the PatientAgent with the appropriate system prompt."""
        super().__init__(prompts.PATIENT_AGENT_PROMPT)
        self.state = {
            "got_name": False,
            "got_dob": False,
            "got_insurance": False,
            "got_insurance_id": False,
            "got_address": False,
            "got_appointment_reason": False,
            "got_symptoms": False,
            "ready_for_hospital_call": False
        }
        self.patient_info = {
            "name": None,
            "dob": None,
            "insurance": None,
            "insurance_id": None,
            "address": None,
            "city": None,
            "state": None,
            "zip_code": None,
            "appointment_reason": None,
            "symptoms": None,
            "preferred_timeframe": None
        }
        self.conversation_counter = 0
    
    def generate_response(self, patient_message, known_info=""):
        """
        Generate a response to the patient's message.
        
        Args:
            patient_message: The patient's message
            known_info: Known information about the patient
            
        Returns:
            str: The generated response
        """
        # Format the user message using the template
        user_message = prompts.PATIENT_AGENT_USER_TEMPLATE.format(
            phone_number=known_info.get("phone_number", "Unknown"),
            known_info=known_info,
            conversation_history=self.get_conversation_summary(),
            patient_message=patient_message
        )
        
        return super().generate_response(user_message)
    
    def _update_state(self, response):
        """
        Update agent state based on the current response.
        Extracts information from the assistant's response.
        
        Args:
            response: The assistant's response
        """
        # Update conversation counter
        self.conversation_counter += 1
        
        # Check for patient name in response
        if not self.state["got_name"]:
            name_match = re.search(r"EXTRACT_NAME: (.+?)(?:\.|$)", response, re.MULTILINE)
            if name_match:
                self.patient_info["name"] = name_match.group(1).strip()
                self.state["got_name"] = True
                logger.info(f"Extracted patient name: {self.patient_info['name']}")
                
                # Remove the extraction line from the response if it was added
                response = re.sub(r"EXTRACT_NAME: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for DOB in response
        if not self.state["got_dob"]:
            dob_match = re.search(r"EXTRACT_DOB: (.+?)(?:\.|$)", response, re.MULTILINE)
            if dob_match:
                self.patient_info["dob"] = dob_match.group(1).strip()
                self.state["got_dob"] = True
                logger.info(f"Extracted patient DOB: {self.patient_info['dob']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_DOB: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for insurance in response
        if not self.state["got_insurance"]:
            insurance_match = re.search(r"EXTRACT_INSURANCE: (.+?)(?:\.|$)", response, re.MULTILINE)
            if insurance_match:
                self.patient_info["insurance"] = insurance_match.group(1).strip()
                self.state["got_insurance"] = True
                logger.info(f"Extracted patient insurance: {self.patient_info['insurance']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_INSURANCE: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for insurance ID in response
        if not self.state["got_insurance_id"] and self.state["got_insurance"]:
            insurance_id_match = re.search(r"EXTRACT_INSURANCE_ID: (.+?)(?:\.|$)", response, re.MULTILINE)
            if insurance_id_match:
                self.patient_info["insurance_id"] = insurance_id_match.group(1).strip()
                self.state["got_insurance_id"] = True
                logger.info(f"Extracted patient insurance ID: {self.patient_info['insurance_id']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_INSURANCE_ID: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for appointment reason in response
        if not self.state["got_appointment_reason"]:
            reason_match = re.search(r"EXTRACT_REASON: (.+?)(?:\.|$)", response, re.MULTILINE)
            if reason_match:
                self.patient_info["appointment_reason"] = reason_match.group(1).strip()
                self.state["got_appointment_reason"] = True
                logger.info(f"Extracted appointment reason: {self.patient_info['appointment_reason']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_REASON: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for symptoms in response
        if not self.state["got_symptoms"] and self.state["got_appointment_reason"]:
            symptoms_match = re.search(r"EXTRACT_SYMPTOMS: (.+?)(?:\.|$)", response, re.MULTILINE)
            if symptoms_match:
                self.patient_info["symptoms"] = symptoms_match.group(1).strip()
                self.state["got_symptoms"] = True
                logger.info(f"Extracted symptoms: {self.patient_info['symptoms']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_SYMPTOMS: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for preferred timeframe in response
        preferred_time_match = re.search(r"EXTRACT_PREFERRED_TIME: (.+?)(?:\.|$)", response, re.MULTILINE)
        if preferred_time_match:
            self.patient_info["preferred_timeframe"] = preferred_time_match.group(1).strip()
            logger.info(f"Extracted preferred timeframe: {self.patient_info['preferred_timeframe']}")
            
            # Remove the extraction line from the response
            response = re.sub(r"EXTRACT_PREFERRED_TIME: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check if we're ready to call the hospital
        if (self.state["got_name"] and 
            self.state["got_dob"] and 
            self.state["got_insurance"] and 
            self.state["got_appointment_reason"] and
            self.conversation_counter >= 2):
            self.state["ready_for_hospital_call"] = True
            logger.info("Patient provided all required information, ready for hospital call")
        
        # Update the conversation history with the cleaned response if needed
        if response != self.conversation_history[-1]["content"]:
            # Replace the last assistant message with the cleaned version
            self.conversation_history[-1]["content"] = response


class HospitalAgent(ConversationAgent):
    """Agent for handling conversations with hospital receptionists."""
    
    def __init__(self, patient_info):
        """
        Initialize the HospitalAgent with the appropriate system prompt.
        
        Args:
            patient_info: Dictionary containing patient information
        """
        super().__init__(prompts.HOSPITAL_AGENT_PROMPT)
        self.patient_info = patient_info
        self.state = {
            "appointment_confirmed": False,
            "got_appointment_date": False,
            "got_appointment_time": False,
            "got_doctor_name": False
        }
        self.appointment_info = {
            "date": None,
            "time": None,
            "doctor": None,
            "special_instructions": None
        }
        self.conversation_counter = 0
    
    def generate_response(self, receptionist_message):
        """
        Generate a response to the receptionist's message.
        
        Args:
            receptionist_message: The receptionist's message
            
        Returns:
            str: The generated response
        """
        # Format the user message using the template
        user_message = prompts.HOSPITAL_AGENT_USER_TEMPLATE.format(
            patient_name=self.patient_info.get("name", "the patient"),
            patient_dob=self.patient_info.get("dob", "unknown date of birth"),
            patient_insurance=self.patient_info.get("insurance", "unknown insurance"),
            patient_insurance_id=self.patient_info.get("insurance_id", "unknown insurance ID"),
            appointment_reason=self.patient_info.get("appointment_reason", "an appointment"),
            symptoms=self.patient_info.get("symptoms", "unspecified symptoms"),
            preferred_timeframe=self.patient_info.get("preferred_timeframe", "as soon as possible"),
            conversation_history=self.get_conversation_summary(),
            receptionist_message=receptionist_message
        )
        
        return super().generate_response(user_message)
    
    def _update_state(self, response):
        """
        Update the state based on the current response.
        Extracts appointment information from the assistant's response.
        
        Args:
            response: The assistant's response
        """
        # Update conversation counter
        self.conversation_counter += 1
        
        # Check for appointment date in response
        if not self.state["got_appointment_date"]:
            date_match = re.search(r"EXTRACT_DATE: (.+?)(?:\.|$)", response, re.MULTILINE)
            if date_match:
                self.appointment_info["date"] = date_match.group(1).strip()
                self.state["got_appointment_date"] = True
                logger.info(f"Extracted appointment date: {self.appointment_info['date']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_DATE: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for appointment time in response
        if not self.state["got_appointment_time"]:
            time_match = re.search(r"EXTRACT_TIME: (.+?)(?:\.|$)", response, re.MULTILINE)
            if time_match:
                self.appointment_info["time"] = time_match.group(1).strip()
                self.state["got_appointment_time"] = True
                logger.info(f"Extracted appointment time: {self.appointment_info['time']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_TIME: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for doctor name in response
        if not self.state["got_doctor_name"]:
            doctor_match = re.search(r"EXTRACT_DOCTOR: (.+?)(?:\.|$)", response, re.MULTILINE)
            if doctor_match:
                self.appointment_info["doctor"] = doctor_match.group(1).strip()
                self.state["got_doctor_name"] = True
                logger.info(f"Extracted doctor name: {self.appointment_info['doctor']}")
                
                # Remove the extraction line from the response
                response = re.sub(r"EXTRACT_DOCTOR: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check for special instructions in response
        special_instructions_match = re.search(r"EXTRACT_INSTRUCTIONS: (.+?)(?:\.|$)", response, re.MULTILINE)
        if special_instructions_match:
            self.appointment_info["special_instructions"] = special_instructions_match.group(1).strip()
            logger.info(f"Extracted special instructions: {self.appointment_info['special_instructions']}")
            
            # Remove the extraction line from the response
            response = re.sub(r"EXTRACT_INSTRUCTIONS: .+?(?:\.|$)", "", response, flags=re.MULTILINE)
        
        # Check if appointment is confirmed
        if (self.state["got_appointment_date"] and 
            self.state["got_appointment_time"] and 
            self.conversation_counter >= 2):
            self.state["appointment_confirmed"] = True
            logger.info("Appointment confirmed with hospital")
        
        # Update the conversation history with the cleaned response if needed
        if response != self.conversation_history[-1]["content"]:
            # Replace the last assistant message with the cleaned version
            self.conversation_history[-1]["content"] = response
    
    def get_appointment_details(self):
        """
        Get the confirmed appointment details.
        
        Returns:
            dict: The appointment details if confirmed, None otherwise
        """
        if self.state["appointment_confirmed"]:
            return {
                "date": self.appointment_info["date"],
                "time": self.appointment_info["time"],
                "doctor": self.appointment_info["doctor"],
                "special_instructions": self.appointment_info["special_instructions"],
                "appointment_confirmed": True
            }
        return None
