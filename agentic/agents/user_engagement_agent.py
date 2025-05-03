"""
User Engagement & Memory Agent for the Agentic Health Assistant system.
This is the entry point agent that handles initial conversations and memory retrieval.
"""
import sys
import logging
from typing import Dict, List, Optional, Any, Union
import re

# Add parent directory to path to import from our own modules
sys.path.append('..')
sys.path.append('../..')
from agents.base_agent import BaseAgent
from schema import AgentState, IntentType, UserProfile
from db_connector import DatabaseConnector
from prompts import USER_ENGAGEMENT_AGENT_PROMPT
import config

logger = logging.getLogger(__name__)

class UserEngagementAgent(BaseAgent):
    """
    Agent responsible for user engagement, memory retrieval, and intent classification.
    This is the initial agent that interacts with users.
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize the User Engagement Agent with appropriate prompt."""
        super().__init__(USER_ENGAGEMENT_AGENT_PROMPT, model_name)
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Process user input, manage conversation memory, and classify intent.
        
        Args:
            state: The current state from the LangGraph
            
        Returns:
            Updated state with user information and intent classification
        """
        # Check if we need to retrieve or create user profile
        if not state.memory.user_profile.user_id:
            # Get or create user profile from database
            phone_number = state.memory.user_profile.phone_number
            user_profile = DatabaseConnector.get_or_create_user(phone_number)
            state.memory.user_profile = user_profile
            
            # Add context about whether this is a new or returning user
            is_new_user = not user_profile.name
            context = "new user" if is_new_user else "returning user"
            logger.info(f"User {phone_number} is a {context}")
            
            # Add system message to provide context to the LLM
            if is_new_user:
                state.system_message = "This is a new user. Please collect their basic information."
            else:
                state.system_message = (
                    f"This is a returning user. Their name is {user_profile.name}. "
                    f"They were born on {user_profile.date_of_birth or 'unknown DOB'}. "
                    f"Their insurance is {user_profile.insurance_provider or 'unknown'}."
                )
        
        # Process with the base agent
        state = super().__call__(state)
        
        # After getting the LLM response, update the user profile if needed
        self._extract_and_update_user_info(state)
        
        # Classify the intent based on the conversation
        state.current_intent = self._classify_intent(state)
        state.memory.current_intent = state.current_intent
        logger.info(f"Classified intent: {state.current_intent}")
        
        return state
    
    def _extract_and_update_user_info(self, state: AgentState) -> None:
        """
        Extract user information from conversation and update the profile.
        
        Args:
            state: The current state with conversation history
        """
        profile = state.memory.user_profile
        conversation = " ".join([msg["content"] for msg in state.memory.conversation_history])
        
        # Basic extraction patterns
        patterns = {
            "name": r"my name is ([A-Za-z\s]+)",
            "date_of_birth": r"(born on|date of birth|DOB).{1,10}(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\w+ \d{1,2},? \d{4})",
            "insurance_provider": r"(insurance|provider).{1,10}(Blue Cross|Aetna|Cigna|UnitedHealthcare|Kaiser|Humana|Medicare|Medicaid|[A-Za-z\s]+)",
            "insurance_id": r"(insurance ID|member number|policy number).{1,10}([A-Za-z0-9\-]+)",
            "zip_code": r"(zip code|ZIP).{1,5}(\d{5})"
        }
        
        updates = {}
        for field, pattern in patterns.items():
            if getattr(profile, field) is None:  # Only extract if not already set
                match = re.search(pattern, conversation, re.IGNORECASE)
                if match:
                    if field == "name":
                        updates[field] = match.group(1).strip()
                    elif field == "date_of_birth":
                        updates[field] = match.group(2).strip()
                    elif field == "insurance_provider":
                        updates[field] = match.group(2).strip()
                    elif field == "insurance_id":
                        updates[field] = match.group(2).strip()
                    elif field == "zip_code":
                        updates[field] = match.group(2).strip()
        
        # Update the state's user profile
        for field, value in updates.items():
            setattr(state.memory.user_profile, field, value)
        
        # Update database if we have any new information
        if updates:
            DatabaseConnector.update_user_profile(state.memory.user_profile)
            logger.info(f"Updated user profile with new information: {updates}")
    
    def _classify_intent(self, state: AgentState) -> IntentType:
        """
        Classify the user's intent based on conversation.
        
        Args:
            state: The current state with conversation history
            
        Returns:
            IntentType: The classified intent
        """
        # Use the latest conversation (last few exchanges) to classify intent
        recent_messages = state.memory.conversation_history[-4:] if len(state.memory.conversation_history) > 4 else state.memory.conversation_history
        recent_text = " ".join([msg["content"] for msg in recent_messages])
        
        # Simple keyword-based classification for now
        # In a production system, we'd use a more robust classifier
        keywords = {
            IntentType.APPOINTMENT_SCHEDULING: [
                "schedule", "appointment", "book", "see a doctor", "meet with", "visit", "slot"
            ],
            IntentType.MEDICAL_ADVICE: [
                "advice", "should I", "recommend", "opinion", "treatment", "diagnosis", "symptoms"
            ],
            IntentType.GENERAL_INFO: [
                "information", "how does", "what is", "tell me about", "explain", "understand"
            ],
            IntentType.FOLLOW_UP: [
                "follow up", "check in", "last time", "previous", "appointment", "visited"
            ],
            IntentType.EMERGENCY: [
                "emergency", "urgent", "severe pain", "bleeding", "difficulty breathing", 
                "chest pain", "unconscious", "911"
            ]
        }
        
        # Count keyword matches for each intent
        intent_scores = {intent: 0 for intent in IntentType}
        for intent, intent_keywords in keywords.items():
            for keyword in intent_keywords:
                if keyword.lower() in recent_text.lower():
                    intent_scores[intent] += 1
        
        # Find the intent with the highest score
        max_score = 0
        classified_intent = IntentType.OTHER
        for intent, score in intent_scores.items():
            if score > max_score:
                max_score = score
                classified_intent = intent
        
        # Special handling for emergency intents - prioritize them
        if intent_scores[IntentType.EMERGENCY] > 0:
            return IntentType.EMERGENCY
            
        return classified_intent
