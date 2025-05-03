"""
Database connector for the Agentic Health Assistant system.
Builds on the existing database models but provides an interface for the LangGraph agents.
"""
import sys
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Add parent directory to path to import from existing codebase
sys.path.append('..')
sys.path.append('../..')

# Import from parent directory modules
from memory_module import MemoryStore
from models import Caller, CallRecord, Hospital

# Import from local schema
from schema import UserProfile, AppointmentDetails, TaskPlan

logger = logging.getLogger(__name__)

class DatabaseConnector:
    """
    Provides an interface for LangGraph agents to interact with the database.
    Builds on the existing MemoryStore but adds methods specific to the agentic system.
    """
    
    @staticmethod
    def get_or_create_user(phone_number: str) -> UserProfile:
        """
        Get a user by phone number or create if not exists.
        
        Args:
            phone_number: The user's phone number
        
        Returns:
            UserProfile: User data in the format used by the agents
        """
        caller = MemoryStore.get_caller(phone_number)
        
        if not caller:
            logger.warning(f"Failed to get or create caller with phone number {phone_number}")
            # Return a basic profile with just the phone number
            return UserProfile(phone_number=phone_number)
        
        # Convert from Caller model to UserProfile schema
        return UserProfile(
            user_id=str(caller.id),
            phone_number=caller.phone_number,
            name=caller.name,
            date_of_birth=caller.date_of_birth,
            insurance_provider=caller.insurance_provider,
            insurance_id=caller.insurance_id,
            address=caller.address,
            city=caller.city,
            state=caller.state,
            zip_code=caller.zip_code,
            created_at=caller.created_at,
            updated_at=caller.updated_at
        )

    @staticmethod
    def update_user_profile(profile: UserProfile) -> bool:
        """
        Update user profile information.
        
        Args:
            profile: The updated UserProfile object
        
        Returns:
            bool: Success status
        """
        updates = {
            'name': profile.name,
            'date_of_birth': profile.date_of_birth,
            'insurance_provider': profile.insurance_provider,
            'insurance_id': profile.insurance_id,
            'address': profile.address,
            'city': profile.city,
            'state': profile.state,
            'zip_code': profile.zip_code
        }
        
        # Filter out None values
        updates = {k: v for k, v in updates.items() if v is not None}
        
        return MemoryStore.update_caller(profile.phone_number, **updates)

    @staticmethod
    def create_call_record(phone_number: str, call_type: str, call_sid: Optional[str] = None) -> Optional[int]:
        """
        Create a new call record.
        
        Args:
            phone_number: The user's phone number
            call_type: Type of call ('inbound' or 'outbound')
            call_sid: Optional Vapi call identifier
        
        Returns:
            int: ID of the created call record, or None on failure
        """
        record = MemoryStore.create_call_record(phone_number, call_type, call_sid)
        return record.id if record else None

    @staticmethod
    def update_call_record(call_id: int, **updates) -> bool:
        """
        Update an existing call record.
        
        Args:
            call_id: ID of the call record
            **updates: Fields to update
        
        Returns:
            bool: Success status
        """
        return MemoryStore.update_call_record(call_id, **updates)

    @staticmethod
    def get_nearby_hospitals(zip_code: str, radius_miles: int = 10) -> List[Dict[str, Any]]:
        """
        Get hospitals near a zip code.
        
        Args:
            zip_code: User's zip code
            radius_miles: Search radius in miles
        
        Returns:
            List[Dict]: List of nearby hospitals
        """
        hospitals = MemoryStore.get_hospitals_by_zip(zip_code, radius_miles)
        
        return [
            {
                "id": hospital.id,
                "name": hospital.name,
                "phone_number": hospital.phone_number,
                "address": hospital.address,
                "zip_code": hospital.zip_code
            }
            for hospital in hospitals
        ]

    @staticmethod
    def save_appointment(user_id: str, appointment: AppointmentDetails) -> Optional[str]:
        """
        Save appointment details to the database.
        
        Args:
            user_id: User's ID
            appointment: Appointment details
        
        Returns:
            str: Appointment ID if successful, None otherwise
        """
        try:
            # Find the call record associated with this appointment process
            # This assumes we're in an active call process
            call_record = MemoryStore.get_active_call_for_caller(int(user_id))
            
            if not call_record:
                logger.warning(f"No active call found for user {user_id}")
                return None
            
            # Update the call record with appointment details
            updates = {
                "appointment_date": appointment.date,
                "appointment_time": appointment.time,
                "doctor_name": appointment.doctor_name,
                "appointment_type": appointment.reason
            }
            
            success = MemoryStore.update_call_record(call_record.id, **updates)
            
            if success:
                # If appointment_id not provided, use call_record.id as a proxy
                appointment_id = appointment.appointment_id or f"apt-{call_record.id}"
                return appointment_id
            
            return None
        except Exception as e:
            logger.error(f"Error saving appointment: {e}")
            return None

    @staticmethod
    def save_task_plan(task_plan: TaskPlan) -> bool:
        """
        Save a task plan to the database.
        
        Args:
            task_plan: The task plan to save
        
        Returns:
            bool: Success status
        """
        try:
            # This could be stored as JSON in a new task_plans table,
            # but for simplicity with existing schema, we'll store it in call_record
            if not task_plan.user_id:
                logger.error("Cannot save task plan: missing user_id")
                return False
                
            # Try to find an active call for this user
            call_record = MemoryStore.get_active_call_for_caller(int(task_plan.user_id))
            
            if not call_record:
                logger.warning(f"No active call found for user {task_plan.user_id}")
                return False
                
            # Store the task plan as JSON in the call_record
            import json
            task_plan_json = json.dumps(task_plan.dict())
            
            return MemoryStore.update_call_record(call_record.id, task_plan_json=task_plan_json)
        except Exception as e:
            logger.error(f"Error saving task plan: {e}")
            return False
