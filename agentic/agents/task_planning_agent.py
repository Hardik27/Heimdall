"""
Task Planning Agent for the Agentic Health Assistant system.
This agent creates structured plans based on user intent.
"""
import sys
import logging
import json
import uuid
from typing import Dict, List, Optional, Any, Union

# Add parent directory to path to import from our own modules
sys.path.append('..')
sys.path.append('../..')
from agents.base_agent import BaseAgent
from schema import AgentState, IntentType, TaskPlan
from prompts import TASK_PLANNING_AGENT_PROMPT
import config

logger = logging.getLogger(__name__)

class TaskPlanningAgent(BaseAgent):
    """
    Agent responsible for creating detailed plans to address user intents.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the Task Planning Agent with appropriate prompt."""
        super().__init__(TASK_PLANNING_AGENT_PROMPT, model_name)
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Create a structured task plan based on the user intent.
        
        Args:
            state: The current state from the LangGraph
            
        Returns:
            Updated state with a task plan
        """
        # Add intent-specific context to the input
        intent_context = self._get_intent_context(state.current_intent)
        user_profile = state.memory.user_profile
        
        # Create context-enriched input for the planner
        planning_input = (
            f"Intent: {state.current_intent}\n"
            f"User Profile: Name: {user_profile.name or 'Unknown'}, "
            f"DOB: {user_profile.date_of_birth or 'Unknown'}, "
            f"Location: {user_profile.zip_code or 'Unknown'}\n"
            f"Context: {intent_context}\n\n"
            "Create a detailed task plan for handling this user request."
        )
        
        # Store the original user input
        original_input = state.user_input
        
        # Replace with planning-specific input
        state.user_input = planning_input
        
        # Process through base agent
        state = super().__call__(state)
        
        # Restore original user input
        state.user_input = original_input
        
        # Extract and structure the task plan
        structured_plan = self._extract_task_plan(state)
        
        # Create a TaskPlan object and add it to the state
        state.task_plan = structured_plan
        
        logger.info(f"Created task plan: {structured_plan.task_id} with {len(structured_plan.steps)} steps")
        
        return state
    
    def _get_intent_context(self, intent: IntentType) -> str:
        """
        Get context-specific guidance based on the intent.
        
        Args:
            intent: The classified user intent
            
        Returns:
            str: Context-specific guidance for the planner
        """
        intent_contexts = {
            IntentType.APPOINTMENT_SCHEDULING: (
                "The user wants to schedule a medical appointment. "
                "Plan for determining specialty needs, location preferences, "
                "availability, and insurance compatibility."
            ),
            IntentType.MEDICAL_ADVICE: (
                "The user is asking for medical advice. Plan for providing "
                "general information while being clear about limitations. "
                "Suggest professional consultation when needed."
            ),
            IntentType.GENERAL_INFO: (
                "The user wants general health information. "
                "Plan for providing clear, evidence-based information "
                "from reliable medical sources."
            ),
            IntentType.FOLLOW_UP: (
                "The user is following up on a previous interaction. "
                "Plan for reviewing history, checking appointment status, "
                "and addressing any new concerns."
            ),
            IntentType.EMERGENCY: (
                "EMERGENCY SITUATION. Plan should focus on advising "
                "immediate professional medical attention and providing "
                "basic first aid guidance only if appropriate."
            ),
            IntentType.OTHER: (
                "The user has a request that doesn't fit standard categories. "
                "Plan for understanding their specific needs and determining "
                "if we can assist or need to redirect them."
            )
        }
        
        return intent_contexts.get(intent, intent_contexts[IntentType.OTHER])
    
    def _extract_task_plan(self, state: AgentState) -> TaskPlan:
        """
        Extract a structured task plan from the LLM response.
        
        Args:
            state: The current state with LLM response
            
        Returns:
            TaskPlan: A structured task plan
        """
        response = state.response_to_user
        
        # Generate a unique ID for this task
        task_id = f"task-{uuid.uuid4().hex[:8]}"
        
        # Get user ID if available
        user_id = state.memory.user_profile.user_id or "unknown"
        
        # Default empty plan
        plan = TaskPlan(
            task_id=task_id,
            task_type=str(state.current_intent),
            user_id=user_id,
            steps=[],
            context={}
        )
        
        # Try to extract steps from the response
        try:
            # Look for patterns like numbered lists (1. Step one, 2. Step two)
            import re
            step_pattern = r'(\d+)[.)] (.+?)(?=\n\d+[.)]|\Z)'
            steps = re.findall(step_pattern, response, re.DOTALL)
            
            if steps:
                plan.steps = [{"step_number": int(num), "description": desc.strip()} for num, desc in steps]
            else:
                # If no numbered steps, try to divide by line breaks
                lines = [line.strip() for line in response.split('\n') if line.strip()]
                plan.steps = [{"step_number": i+1, "description": line} for i, line in enumerate(lines)]
            
            # Extract potential context information
            context_sections = {
                "Goal": r'Goal:\s*(.+?)(?=\n\w+:|$)',
                "Required Information": r'Required Information:\s*(.+?)(?=\n\w+:|$)',
                "External Systems": r'External Systems:\s*(.+?)(?=\n\w+:|$)',
                "Success Criteria": r'Success Criteria:\s*(.+?)(?=\n\w+:|$)'
            }
            
            context = {}
            for key, pattern in context_sections.items():
                match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
                if match:
                    context[key] = match.group(1).strip()
            
            plan.context = context
            
        except Exception as e:
            logger.error(f"Error extracting task plan: {e}")
            # Create a simple fallback plan
            plan.steps = [{"step_number": 1, "description": "Process user request"}]
            plan.context = {"Note": "Failed to extract structured plan"}
        
        return plan
