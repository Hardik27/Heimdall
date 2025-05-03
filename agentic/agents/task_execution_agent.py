"""
Task Execution Agent for the Agentic Health Assistant system.
This agent executes plans and interacts with external systems.
"""
import sys
import logging
from typing import Dict, List, Optional, Any, Union
import json

# Add parent directory to path to import from our own modules
sys.path.append('..')
sys.path.append('../..')
from agents.base_agent import BaseAgent
from schema import AgentState, IntentType, AppointmentDetails
from db_connector import DatabaseConnector
from prompts import TASK_EXECUTION_AGENT_PROMPT
import config

# Import telephony handler for outbound calls
from telephony_handler import TelephonyHandler

logger = logging.getLogger(__name__)

class TaskExecutionAgent(BaseAgent):
    """
    Agent responsible for executing task plans and interacting with external systems.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the Task Execution Agent with appropriate prompt."""
        super().__init__(TASK_EXECUTION_AGENT_PROMPT, model_name)
        self.telephony_handler = TelephonyHandler()
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Execute a task plan and interact with external systems as needed.
        
        Args:
            state: The current state from the LangGraph
            
        Returns:
            Updated state with execution results
        """
        # Check if we have a task plan to execute
        if not state.task_plan:
            state.error = "No task plan provided to task execution agent"
            return state
        
        # Get the current step to execute
        current_step_idx = state.task_plan.current_step_index
        if current_step_idx >= len(state.task_plan.steps):
            # All steps completed
            state.task_plan.status = "completed"
            return state
        
        current_step = state.task_plan.steps[current_step_idx]
        
        # Prepare execution context for the agent
        execution_input = (
            f"Task: {state.task_plan.task_type}\n"
            f"Current Step ({current_step_idx + 1}/{len(state.task_plan.steps)}): {current_step['description']}\n"
            f"User Profile: {state.memory.user_profile.name or 'Unknown'}, "
            f"DOB: {state.memory.user_profile.date_of_birth or 'Unknown'}\n\n"
            "Execute this step and report results."
        )
        
        # Store original input
        original_input = state.user_input
        
        # Set execution-specific input
        state.user_input = execution_input
        
        # Process through base agent to get execution plan
        state = super().__call__(state)
        
        # Restore original input
        state.user_input = original_input
        
        # Check if external action is needed (like outbound call)
        if self._needs_external_action(state):
            # Perform the external action
            result = self._perform_external_action(state)
            state.external_call_result = result
            
            # Update the agent with the result
            result_input = (
                f"External Action Result: {json.dumps(result, indent=2)}\n\n"
                "Process this result and determine next steps."
            )
            state.user_input = result_input
            state = super().__call__(state)
            state.user_input = original_input
        
        # Mark this step as completed and advance to next step
        state.task_plan.current_step_index += 1
        
        # Update task status
        if state.task_plan.current_step_index >= len(state.task_plan.steps):
            state.task_plan.status = "completed"
        else:
            state.task_plan.status = "in_progress"
        
        # If we completed an appointment step, extract appointment details
        if state.current_intent == IntentType.APPOINTMENT_SCHEDULING and state.external_call_result:
            appointment = self._extract_appointment_details(state)
            if appointment:
                state.appointment_details = appointment
                # Save to database
                appointment_id = DatabaseConnector.save_appointment(
                    state.memory.user_profile.user_id, 
                    appointment
                )
                if appointment_id:
                    state.appointment_details.appointment_id = appointment_id
        
        return state
    
    def _needs_external_action(self, state: AgentState) -> bool:
        """
        Determine if the current step requires external action.
        
        Args:
            state: The current agent state
            
        Returns:
            bool: True if external action is needed
        """
        # Get the current step
        if not state.task_plan or state.task_plan.current_step_index >= len(state.task_plan.steps):
            return False
            
        current_step = state.task_plan.steps[state.task_plan.current_step_index]
        step_desc = current_step['description'].lower()
        
        # Keywords indicating external actions
        external_action_keywords = [
            "call", "contact", "phone", "appointment", "schedule", "book", 
            "hospital", "doctor", "clinic", "outbound", "external"
        ]
        
        # Check if any keywords are present
        return any(keyword in step_desc for keyword in external_action_keywords)
    
    def _perform_external_action(self, state: AgentState) -> Dict[str, Any]:
        """
        Perform an external action like making an outbound call.
        
        Args:
            state: The current agent state
            
        Returns:
            Dict: Result of the external action
        """
        # In a real implementation, this would connect to actual services
        # For now, we'll simulate based on the intent
        
        if state.current_intent == IntentType.APPOINTMENT_SCHEDULING:
            # Simulate making an outbound call to a hospital
            user_profile = state.memory.user_profile
            patient_info = {
                "name": user_profile.name or "Patient",
                "dob": user_profile.date_of_birth or "Unknown",
                "insurance": user_profile.insurance_provider or "Unknown",
                "reason": "Checkup"  # Could extract from conversation
            }
            
            # Use the existing TelephonyHandler to simulate a call
            appointment = self.telephony_handler.simulate_hospital_conversation(patient_info)
            return {
                "action": "outbound_call",
                "target": "hospital",
                "status": "successful",
                "appointment": appointment
            }
        
        elif state.current_intent == IntentType.MEDICAL_ADVICE:
            # Simulate looking up medical information
            return {
                "action": "information_lookup",
                "source": "medical_database",
                "status": "successful",
                "information": "Medical advice information would be here."
            }
        
        elif state.current_intent == IntentType.GENERAL_INFO:
            # Simulate retrieving general information
            return {
                "action": "information_lookup",
                "source": "knowledge_base",
                "status": "successful",
                "information": "General health information would be here."
            }
        
        else:
            # Generic simulation for other intents
            return {
                "action": "generic_task",
                "status": "completed",
                "notes": "Simulated task execution for development purposes."
            }
    
    def _extract_appointment_details(self, state: AgentState) -> Optional[AppointmentDetails]:
        """
        Extract structured appointment details from execution results.
        
        Args:
            state: The current state with execution results
            
        Returns:
            Optional[AppointmentDetails]: Extracted appointment details
        """
        # Try to get appointment info from external call result
        if not state.external_call_result or 'appointment' not in state.external_call_result:
            return None
            
        appointment_data = state.external_call_result['appointment']
        
        # Create structured appointment object
        appointment = AppointmentDetails(
            doctor_name=appointment_data.get('doctor_name'),
            facility_name="General Hospital",  # Would come from real data
            date=appointment_data.get('date'),
            time=appointment_data.get('time'),
            reason="Medical checkup",  # Would be extracted from conversation
            status="confirmed"
        )
        
        return appointment
