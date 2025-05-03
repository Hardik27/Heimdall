"""
Integration module to bridge the existing non-agentic codebase with the LangGraph-based agentic system.
"""
import sys
import logging
import json
from typing import Dict, Any, Optional

# Add parent directory to path to import from existing codebase
sys.path.append('..')
import config
from voice_assistant import VoiceAssistant
from telephony_handler import TelephonyHandler
from memory_module import MemoryStore

# Import agentic components
from agentic.health_assistant import health_assistant

logger = logging.getLogger(__name__)

class HealthAssistantIntegration:
    """
    Integration layer that decides whether to use the non-agentic or agentic system
    based on configuration and gradual rollout strategy.
    """
    
    def __init__(self):
        """Initialize both systems and integration components."""
        # Initialize legacy components
        self.voice_assistant = VoiceAssistant()
        self.telephony_handler = TelephonyHandler()
        
        # Feature flag for agentic system
        self.use_agentic = getattr(config, 'USE_AGENTIC_SYSTEM', False)
        
        # Initialize any bridges between the systems
        self._init_bridges()
    
    def _init_bridges(self):
        """Initialize bridges between the systems."""
        # Here we could set up any data sync mechanisms, event handlers, etc.
        logger.info(f"Initialized integration bridges with agentic mode: {self.use_agentic}")
    
    def handle_inbound_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle an inbound call, routing to appropriate system.
        
        Args:
            call_data: Call data from webhook
            
        Returns:
            dict: Response for webhook
        """
        phone_number = call_data.get('from') or call_data.get('customer', {}).get('number')
        
        # Determine whether to use agentic system for this call
        should_use_agentic = self._should_use_agentic(phone_number)
        
        if should_use_agentic:
            logger.info(f"Using agentic system for call from {phone_number}")
            return health_assistant.process_inbound_call(call_data)
        else:
            logger.info(f"Using legacy system for call from {phone_number}")
            return self.telephony_handler.handle_inbound_call(call_data)
    
    def place_outbound_call(self, phone_number: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Place an outbound call using the appropriate system.
        
        Args:
            phone_number: Phone number to call
            context: Call context
            
        Returns:
            dict: Call information if successful
        """
        # Determine whether to use agentic system for this call
        should_use_agentic = self._should_use_agentic(phone_number)
        
        if should_use_agentic:
            logger.info(f"Using agentic system for outbound call to {phone_number}")
            return health_assistant.place_outbound_call(phone_number, context)
        else:
            logger.info(f"Using legacy system for outbound call to {phone_number}")
            return self.telephony_handler.place_outbound_call(phone_number, context)
    
    def _should_use_agentic(self, phone_number: str) -> bool:
        """
        Determine whether to use the agentic system for a particular user.
        This allows for gradual rollout and A/B testing strategies.
        
        Args:
            phone_number: The user's phone number
            
        Returns:
            bool: True if should use agentic system
        """
        # Global override
        if not self.use_agentic:
            return False
        
        # Check for any user-specific overrides from the database
        try:
            caller = MemoryStore.get_caller(phone_number)
            if caller:
                # Check if this user has a specific flag in their record
                # This would require extending the Caller model with additional fields
                pass
        except Exception as e:
            logger.error(f"Error checking caller preferences: {e}")
        
        # Gradual rollout logic based on phone number hash
        # This ensures the same user always gets the same experience
        phone_hash = hash(phone_number) % 100  # 0-99
        
        # Rollout percentage - adjust as needed
        agentic_rollout_percent = getattr(config, 'AGENTIC_ROLLOUT_PERCENT', 0)
        
        return phone_hash < agentic_rollout_percent


# Singleton instance
integration = HealthAssistantIntegration()
