"""
Final Agent for the Agentic Health Assistant system.
This agent ensures proper task closure and provides summaries to the user.
"""
import sys
import logging
from typing import Dict, List, Optional, Any, Union

# Add parent directory to path to import from our own modules
sys.path.append('..')
sys.path.append('../..')
from agents.base_agent import BaseAgent
from schema import AgentState, IntentType
from prompts import FINAL_AGENT_PROMPT
import config

logger = logging.getLogger(__name__)

class FinalAgent(BaseAgent):
    """
    Agent responsible for providing closure to tasks and summarizing outcomes.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the Final Agent with appropriate prompt."""
        super().__init__(FINAL_AGENT_PROMPT, model_name)
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Provide closure and summarize completed tasks.
        
        Args:
            state: The current state from the LangGraph
            
        Returns:
            Updated state with closure information
        """
        # Prepare a summary of what was accomplished
        summary = self._generate_summary(state)
        
        # Create input for the final agent
        final_input = (
            f"Task Completed: {state.current_intent}\n"
            f"Summary: {summary}\n\n"
            "Provide a clear summary for the user and appropriate closure."
        )
        
        # Store original input
        original_input = state.user_input
        
        # Use our summary as input
        state.user_input = final_input
        
        # Process through base agent
        state = super().__call__(state)
        
        # Restore original input
        state.user_input = original_input
        
        # Mark as completed
        state.completed = True
        
        # If we have task_plan, update its status
        if state.task_plan:
            state.task_plan.status = "completed"
        
        logger.info(f"Task completed and summarized for user: {state.current_intent}")
        
        return state
    
    def _generate_summary(self, state: AgentState) -> str:
        """
        Generate a summary of the completed task.
        
        Args:
            state: The current state
            
        Returns:
            str: A summary of what was accomplished
        """
        # Different summaries based on intent and results
        if state.current_intent == IntentType.APPOINTMENT_SCHEDULING and state.appointment_details:
            # Appointment scheduling summary
            apt = state.appointment_details
            summary = (
                f"Successfully scheduled an appointment with {apt.doctor_name} "
                f"for {apt.date} at {apt.time}. "
                f"The appointment is for: {apt.reason or 'medical consultation'}."
            )
            
            # Add extra details if available
            if apt.facility_name:
                summary += f" The appointment is at {apt.facility_name}."
            
            if apt.facility_address:
                summary += f" Located at: {apt.facility_address}."
                
            if apt.notes:
                summary += f" Special instructions: {apt.notes}"
                
            return summary
            
        elif state.current_intent == IntentType.MEDICAL_ADVICE:
            # Medical advice summary
            return (
                "Provided health information based on your questions. "
                "Remember that this advice is general in nature and not a substitute "
                "for professional medical consultation."
            )
            
        elif state.current_intent == IntentType.GENERAL_INFO:
            # General info summary
            return "Provided general health information based on your request."
            
        elif state.current_intent == IntentType.FOLLOW_UP:
            # Follow-up summary
            return "Completed follow-up on your previous interaction and provided relevant updates."
            
        elif state.current_intent == IntentType.EMERGENCY:
            # Emergency summary
            return (
                "Provided guidance for your urgent situation. "
                "Remember to seek immediate professional medical attention if you "
                "are experiencing a medical emergency."
            )
            
        else:
            # Generic summary
            return "Successfully completed your request. Thank you for using our health assistant."
