"""
Memory Module for Tofia Voice Assistant.
Handles database operations for storing and retrieving caller information and call records.
"""
import logging
from sqlalchemy.exc import SQLAlchemyError
from models import get_session, Caller, CallRecord

logger = logging.getLogger(__name__)

class MemoryStore:
    """Handles persistence of caller profiles and call records."""
    
    @staticmethod
    def get_caller(phone_number):
        """
        Retrieve a caller by phone number or create a new record if not found.
        
        Args:
            phone_number: The caller's phone number
            
        Returns:
            Caller: The caller object from the database
        """
        session = get_session()
        try:
            # Try to find existing caller
            caller = session.query(Caller).filter(Caller.phone_number == phone_number).first()
            
            # If not found, create new caller record
            if not caller:
                logger.info(f"Creating new caller record for {phone_number}")
                caller = Caller(phone_number=phone_number)
                session.add(caller)
                session.commit()
            
            # Create a detached copy of the caller to avoid session issues
            caller_copy = Caller(
                id=caller.id,
                phone_number=caller.phone_number,
                name=caller.name,
                date_of_birth=caller.date_of_birth,
                insurance_provider=caller.insurance_provider,
                created_at=caller.created_at,
                updated_at=caller.updated_at
            )
            
            return caller_copy
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving caller: {e}")
            session.rollback()
            # Return a temporary caller object for fallback
            return Caller(phone_number=phone_number)
        finally:
            session.close()
    
    @staticmethod
    def update_caller(phone_number, **updates):
        """
        Update caller information.
        
        Args:
            phone_number: The caller's phone number
            **updates: Dictionary of fields to update
            
        Returns:
            bool: Success status of the update
        """
        session = get_session()
        try:
            caller = session.query(Caller).filter(Caller.phone_number == phone_number).first()
            if not caller:
                logger.warning(f"Attempted to update non-existent caller: {phone_number}")
                return False
            
            # Update only provided fields
            for field, value in updates.items():
                if hasattr(caller, field):
                    setattr(caller, field, value)
            
            session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error updating caller: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    def create_call_record(phone_number, call_type, call_sid=None):
        """
        Create a new call record for a caller.
        
        Args:
            phone_number: The caller's phone number
            call_type: Type of call ('inbound' or 'outbound')
            call_sid: Optional Vapi call identifier
            
        Returns:
            CallRecord: The created call record
        """
        session = get_session()
        try:
            # Get or create caller
            caller_session = get_session()
            try:
                caller = caller_session.query(Caller).filter(Caller.phone_number == phone_number).first()
                if not caller:
                    caller = Caller(phone_number=phone_number)
                    caller_session.add(caller)
                    caller_session.commit()
                caller_id = caller.id
            finally:
                caller_session.close()
            
            # Create new call record
            call_record = CallRecord(
                caller_id=caller_id,
                call_type=call_type,
                call_sid=call_sid
            )
            session.add(call_record)
            session.commit()
            
            # Create a detached copy to return
            record_copy = CallRecord(
                id=call_record.id,
                caller_id=call_record.caller_id,
                call_type=call_record.call_type,
                call_sid=call_record.call_sid,
                start_time=call_record.start_time,
                status=call_record.status
            )
            
            return record_copy
        except SQLAlchemyError as e:
            logger.error(f"Database error creating call record: {e}")
            session.rollback()
            return None
        finally:
            session.close()
    
    @staticmethod
    def update_call_record(call_id, **updates):
        """
        Update an existing call record.
        
        Args:
            call_id: ID of the call record to update
            **updates: Dictionary of fields to update
            
        Returns:
            bool: Success status of the update
        """
        session = get_session()
        try:
            call_record = session.query(CallRecord).filter(CallRecord.id == call_id).first()
            if not call_record:
                logger.warning(f"Attempted to update non-existent call record: {call_id}")
                return False
            
            # Update only provided fields
            for field, value in updates.items():
                if hasattr(call_record, field):
                    setattr(call_record, field, value)
            
            session.commit()
            return True
        except SQLAlchemyError as e:
            logger.error(f"Database error updating call record: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    def get_recent_calls(phone_number, limit=5):
        """
        Get recent calls for a caller.
        
        Args:
            phone_number: The caller's phone number
            limit: Maximum number of calls to return
            
        Returns:
            list: List of recent CallRecord objects
        """
        session = get_session()
        try:
            caller = session.query(Caller).filter(Caller.phone_number == phone_number).first()
            if not caller:
                return []
            
            calls = session.query(CallRecord).filter(
                CallRecord.caller_id == caller.id
            ).order_by(CallRecord.start_time.desc()).limit(limit).all()
            
            # Create detached copies of the records
            result = []
            for call in calls:
                call_copy = CallRecord(
                    id=call.id,
                    caller_id=call.caller_id,
                    call_type=call.call_type,
                    call_sid=call.call_sid,
                    start_time=call.start_time,
                    end_time=call.end_time,
                    summary=call.summary,
                    status=call.status,
                    appointment_date=call.appointment_date,
                    appointment_time=call.appointment_time,
                    doctor_name=call.doctor_name,
                    appointment_type=call.appointment_type
                )
                result.append(call_copy)
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving call records: {e}")
            return []
        finally:
            session.close()
