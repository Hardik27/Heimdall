"""
Schema definitions for the Agentic Health Assistant system.
"""
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime


class IntentType(str, Enum):
    """Types of user intents that the system can handle."""
    GENERAL_INFO = "general_info"
    APPOINTMENT_SCHEDULING = "appointment_scheduling"
    MEDICAL_ADVICE = "medical_advice"
    FOLLOW_UP = "follow_up"
    EMERGENCY = "emergency"
    OTHER = "other"


class UserProfile(BaseModel):
    """User information stored in the system."""
    user_id: Optional[str] = None
    phone_number: str
    name: Optional[str] = None
    date_of_birth: Optional[str] = None  # Format: YYYY-MM-DD
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    known_health_conditions: Optional[List[str]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        frozen = False


class ConversationMemory(BaseModel):
    """Conversation memory for recall across agent interactions."""
    conversation_id: str
    user_profile: UserProfile
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    current_intent: Optional[IntentType] = None
    last_agent_state: Optional[str] = None

    class Config:
        frozen = False


class AppointmentDetails(BaseModel):
    """Details of a medical appointment."""
    appointment_id: Optional[str] = None
    doctor_name: Optional[str] = None
    specialty: Optional[str] = None
    facility_name: Optional[str] = None
    facility_address: Optional[str] = None
    facility_phone: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    duration_minutes: Optional[int] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = "pending"  # pending, confirmed, rescheduled, canceled

    class Config:
        frozen = False


class TaskPlan(BaseModel):
    """Plan for executing a task on behalf of the user."""
    task_id: str
    task_type: str
    user_id: str
    steps: List[Dict[str, Any]] = Field(default_factory=list)
    current_step_index: int = 0
    context: Dict[str, Any] = Field(default_factory=dict)
    status: str = "pending"  # pending, in_progress, completed, failed

    class Config:
        frozen = False


class AgentState(BaseModel):
    """State passed between agents in the LangGraph."""
    memory: ConversationMemory
    user_input: Optional[str] = None
    system_message: Optional[str] = None
    current_agent: Optional[str] = None
    task_plan: Optional[TaskPlan] = None
    appointment_details: Optional[AppointmentDetails] = None
    current_intent: Optional[IntentType] = None
    response_to_user: Optional[str] = None
    needs_external_call: bool = False
    external_call_result: Optional[Dict[str, Any]] = None
    completed: bool = False
    error: Optional[str] = None

    class Config:
        frozen = False
