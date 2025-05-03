"""
Memory Module for Tofia Voice Assistant.
Handles database operations for storing and retrieving caller information and call records.
"""
import logging
import json
from sqlalchemy.exc import SQLAlchemyError
from models import get_session, Caller, CallRecord, Hospital
from datetime import datetime

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
            return None
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
            
            # Update the updated_at timestamp
            caller.updated_at = datetime.utcnow()
            
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
    def get_call_record(call_id):
        """
        Get a call record by ID.
        
        Args:
            call_id: ID of the call record
            
        Returns:
            CallRecord: The call record if found, None otherwise
        """
        session = get_session()
        try:
            call_record = session.query(CallRecord).filter(CallRecord.id == call_id).first()
            if not call_record:
                return None
                
            # Create a detached copy to return
            record_copy = CallRecord(
                id=call_record.id,
                caller_id=call_record.caller_id,
                call_type=call_record.call_type,
                call_sid=call_record.call_sid,
                start_time=call_record.start_time,
                end_time=call_record.end_time,
                summary=call_record.summary,
                status=call_record.status,
                appointment_date=call_record.appointment_date,
                appointment_time=call_record.appointment_time,
                doctor_name=call_record.doctor_name,
                appointment_type=call_record.appointment_type
            )
            
            return record_copy
                
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving call record: {e}")
            return None
        finally:
            session.close()
    
    @staticmethod
    def save_conversation_history(call_id, conversation_type, user_message, assistant_response):
        """
        Save conversation history to a call record.
        
        Args:
            call_id: ID of the call record
            conversation_type: Type of conversation ('patient' or 'hospital')
            user_message: Message from the user
            assistant_response: Response from the assistant
            
        Returns:
            bool: Success status of the operation
        """
        if not call_id:
            logger.error("Cannot save conversation history: call_id is required")
            return False
            
        session = get_session()
        try:
            # Get the call record
            call_record = session.query(CallRecord).filter(CallRecord.id == call_id).first()
            if not call_record:
                logger.error(f"Call record not found: {call_id}")
                return False
                
            # Get current summary or initialize empty
            current_summary = call_record.summary or ""
            
            # Format the conversation entry with timestamp
            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            new_entry = f"\n[{timestamp} - {conversation_type.upper()}]\nUser: {user_message}\nAssistant: {assistant_response}"
            
            # Update the summary with the new conversation entry
            call_record.summary = current_summary + new_entry
            
            # If the conversation history is getting very large, we can truncate it
            if len(call_record.summary) > 10000:  # Arbitrary limit to prevent excessive DB growth
                logger.warning(f"Truncating conversation history for call {call_id} - exceeds 10000 chars")
                # Keep the beginning and the most recent entries
                call_record.summary = call_record.summary[:2000] + "\n[...TRUNCATED...]\n" + call_record.summary[-8000:]
            
            session.commit()
            logger.info(f"Saved conversation history for call {call_id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving conversation history: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    @staticmethod
    def append_conversation_json(call_id, conversation_type, user_message, assistant_response):
        """
        Append conversation as JSON to a call record for structured storage.
        
        Args:
            call_id: ID of the call record
            conversation_type: Type of conversation ('patient' or 'hospital')
            user_message: Message from the user
            assistant_response: Response from the assistant
            
        Returns:
            bool: Success status of the operation
        """
        if not call_id:
            logger.error("Cannot save conversation: call_id is required")
            return False
            
        session = get_session()
        try:
            # Get the call record
            call_record = session.query(CallRecord).filter(CallRecord.id == call_id).first()
            if not call_record:
                logger.error(f"Call record not found: {call_id}")
                return False
            
            # Initialize the JSON conversation field if needed
            if not call_record.conversation_json:
                call_record.conversation_json = json.dumps([])
                
            # Parse current conversation JSON
            try:
                conversation = json.loads(call_record.conversation_json)
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, start with an empty list
                conversation = []
                
            # Add new message entry
            entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "type": conversation_type,
                "user_message": user_message,
                "assistant_response": assistant_response
            }
            conversation.append(entry)
            
            # Update record with new JSON
            call_record.conversation_json = json.dumps(conversation)
            
            session.commit()
            logger.info(f"Saved structured conversation entry for call {call_id}")
            return True
            
        except SQLAlchemyError as e:
            logger.error(f"Database error saving structured conversation: {e}")
            session.rollback()
            return False
        except Exception as e:
            logger.error(f"Error saving structured conversation: {e}")
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
                result.append(CallRecord(
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
                ))
            
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving recent calls: {e}")
            return []
        finally:
            session.close()
    
    @staticmethod
    def get_hospitals_by_zip(zip_code, limit=5):
        """
        Find hospitals by ZIP code.
        
        Args:
            zip_code: The ZIP code to search for
            limit: Maximum number of hospitals to return
            
        Returns:
            list: List of Hospital objects matching the ZIP code
        """
        if not zip_code:
            logger.warning("Cannot find hospitals: missing ZIP code")
            return []
            
        session = get_session()
        try:
            hospitals = session.query(Hospital).filter(
                Hospital.zip_code == zip_code
            ).limit(limit).all()
            
            # Create detached copies
            result = []
            for hospital in hospitals:
                result.append(Hospital(
                    id=hospital.id,
                    name=hospital.name,
                    phone_number=hospital.phone_number,
                    zip_code=hospital.zip_code,
                    address=hospital.address,
                    created_at=hospital.created_at,
                    updated_at=hospital.updated_at
                ))
            
            logger.info(f"Found {len(result)} hospitals in ZIP code {zip_code}")
            return result
        except SQLAlchemyError as e:
            logger.error(f"Database error retrieving hospitals: {e}")
            return []
        finally:
            session.close()
    
    @staticmethod
    def get_nearest_hospitals(patient_zip, limit=3):
        """
        Find nearest hospitals to the patient's ZIP code.
        In a real implementation, this would use geolocation.
        For now, we're just matching the exact ZIP code.
        
        Args:
            patient_zip: The patient's ZIP code
            limit: Maximum number of hospitals to return
            
        Returns:
            list: List of Hospital objects
        """
        # Get hospitals in the same ZIP code
        hospitals = MemoryStore.get_hospitals_by_zip(patient_zip, limit)
        
        # If no hospitals found in the exact ZIP code, we would normally 
        # expand the search to nearby ZIP codes, but for this simple implementation
        # we'll just return all hospitals if none match the exact ZIP
        if not hospitals:
            session = get_session()
            try:
                hospitals = session.query(Hospital).limit(limit).all()
                
                # Create detached copies
                result = []
                for hospital in hospitals:
                    result.append(Hospital(
                        id=hospital.id,
                        name=hospital.name,
                        phone_number=hospital.phone_number,
                        zip_code=hospital.zip_code,
                        address=hospital.address,
                        created_at=hospital.created_at,
                        updated_at=hospital.updated_at
                    ))
                
                logger.info(f"No hospitals found in ZIP {patient_zip}, returning {len(result)} hospitals from database")
                return result
            except SQLAlchemyError as e:
                logger.error(f"Database error retrieving hospitals: {e}")
                return []
            finally:
                session.close()
        
        return hospitals
