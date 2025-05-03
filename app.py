"""
FastAPI application for Tofia Voice Assistant.
Implements webhook endpoints for Vapi.ai integration.
"""
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import init_db
from voice_assistant import VoiceAssistant
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create FastAPI application
app = FastAPI(title="Tofia Voice Assistant API")

# Add CORS middleware to handle OPTIONS requests from Vapi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Create voice assistant instance
tofia = VoiceAssistant()

# Define root endpoint handlers
@app.get("/")
async def root_get():
    """Health check endpoint for GET requests."""
    return {"status": "healthy", "service": "Tofia Voice Assistant"}

@app.post("/")
async def root_post(request: Request):
    """
    Root POST endpoint to handle Vapi webhooks.
    This serves as a catchall for Vapi requests that might be sent to the root path.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Response for Vapi
    """
    try:
        data = await request.json()
        logger.info(f"Received POST to root endpoint: {data}")
        
        # Try to determine what type of request this is based on the payload
        if "call_id" in data or "call_sid" in data:
            # This might be a conversation webhook
            call_sid = data.get("call_id") or data.get("call_sid")
            message = data.get("transcript", "")
            
            if message:
                # Process as a patient message by default
                logger.info(f"Processing as patient conversation from root endpoint")
                response = tofia.process_patient_message(call_sid, message)
                return response
        
        # Generic success response for other types of requests
        return {"status": "success", "message": "Request received"}
    
    except Exception as e:
        logger.error(f"Error processing root POST request: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/status-update")
async def status_update_direct(request: Request):
    """Direct endpoint for status updates without /api prefix."""
    try:
        data = await request.json()
        logger.info(f"Received status update at direct endpoint: {data}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing status update: {e}")
        return {"status": "success"}  # Always return success to avoid Vapi retries

@app.post("/speech-update")  
async def speech_update_direct(request: Request):
    """Direct endpoint for speech updates without /api prefix."""
    try:
        data = await request.json()
        logger.info(f"Received speech update at direct endpoint: {data}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing speech update: {e}")
        return {"status": "success"}  # Always return success to avoid Vapi retries

@app.post("/conversation-update")
async def conversation_update_direct(request: Request):
    """Direct endpoint for conversation updates without /api prefix."""
    try:
        data = await request.json()
        logger.info(f"Received conversation update at direct endpoint: {data}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error processing conversation update: {e}")
        return {"status": "success"}  # Always return success to avoid Vapi retries

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Tofia Voice Assistant"}

@app.post("/api/incoming_call")
async def incoming_call(request: Request):
    """
    Webhook endpoint for incoming calls from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Response for Vapi
    """
    try:
        call_data = await request.json()
        logger.info(f"Received incoming call webhook: {call_data}")
        
        response = tofia.handle_incoming_call(call_data)
        return response
    
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/patient_conversation")
async def patient_conversation(request: Request):
    """
    Webhook endpoint for patient conversation messages from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Response for Vapi
    """
    try:
        data = await request.json()
        logger.info(f"Received patient conversation webhook: {data}")
        
        # Check if this is a schema validation request from Vapi
        if "type" in data and data.get("type") == "object" and "properties" in data:
            # This is a schema validation request, return a success response
            logger.info("Received schema validation request from Vapi")
            return {"status": "success", "message": "Schema validation successful"}
        
        # Extract data from the actual call
        # Vapi might send call_id or call_sid depending on configuration
        call_sid = data.get("call_id") or data.get("call_sid")
        message = data.get("transcript", "")
        
        if not call_sid:
            logger.warning("Missing call_sid in request, generating mock response")
            return {
                "response": "I'm sorry, but I couldn't process that request. Could you please try again?",
                "end_call": False
            }
        
        response = tofia.process_patient_message(call_sid, message)
        return response
    
    except Exception as e:
        logger.error(f"Error processing patient message: {e}")
        return {
            "response": "I apologize, but I'm having trouble processing your request. Let me try a different approach.",
            "end_call": False
        }

@app.post("/api/hospital_conversation")
async def hospital_conversation(request: Request):
    """
    Webhook endpoint for hospital conversation messages from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Response for Vapi
    """
    try:
        data = await request.json()
        logger.info(f"Received hospital conversation webhook: {data}")
        
        # Check if this is a schema validation request from Vapi
        if "type" in data and data.get("type") == "object" and "properties" in data:
            # This is a schema validation request, return a success response
            logger.info("Received schema validation request from Vapi")
            return {"status": "success", "message": "Schema validation successful"}
        
        # Extract data from the actual call
        # Vapi might send call_id or call_sid depending on configuration
        call_sid = data.get("call_id") or data.get("call_sid")
        message = data.get("transcript", "")
        patient_info = data.get("patient_info", {})
        
        if not call_sid:
            logger.warning("Missing call_sid in request, generating mock response")
            return {
                "response": "I'm sorry, but I couldn't process that request. Could you please try again?",
                "end_call": False
            }
        
        response = tofia.process_hospital_message(call_sid, message)
        return response
    
    except Exception as e:
        logger.error(f"Error processing hospital message: {e}")
        return {
            "response": "I apologize, but I'm having trouble with this conversation. Let me try a different approach.",
            "end_call": False
        }

@app.post("/api/handle_hospital_call")
async def handle_hospital_call(request: Request):
    """
    Webhook endpoint for handling hospital call transfers from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Response for Vapi
    """
    try:
        data = await request.json()
        logger.info(f"Received hospital call transfer request: {data}")
        
        # Check if this is a schema validation request from Vapi
        if "type" in data and data.get("type") == "object" and "properties" in data:
            # This is a schema validation request, return a success response
            logger.info("Received schema validation request from Vapi")
            return {"status": "success", "message": "Schema validation successful"}
        
        # Extract transfer information
        patient_call_id = data.get("patient_call_id")
        hospital_phone = data.get("hospital_phone")
        patient_info = data.get("patient_info", {})
        
        if not patient_call_id or not hospital_phone:
            logger.warning("Missing required fields in hospital transfer request")
            return {
                "status": "error", 
                "message": "Missing required fields patient_call_id or hospital_phone"
            }
        
        # Make the actual hospital call
        call_result = tofia.handle_hospital_call(
            patient_call_id, 
            patient_info.get("phone_number", ""), 
            patient_info
        )
        
        return {
            "status": "success",
            "call_initiated": True,
            "hospital_call_id": call_result.get("call_sid") if call_result else None
        }
    
    except Exception as e:
        logger.error(f"Error handling hospital call transfer: {e}")
        return {
            "status": "error",
            "message": str(e)
        }

@app.post("/call_status")
async def call_status(request: Request):
    """
    Webhook endpoint for call status updates from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Acknowledgement response
    """
    try:
        status_data = await request.json()
        logger.info(f"Received call status webhook: {status_data}")
        
        tofia.handle_call_status_update(status_data)
        return {"status": "received"}
    
    except Exception as e:
        logger.error(f"Error handling call status update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/status-update")
async def status_update(request: Request):
    """
    Webhook endpoint for status updates from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Acknowledgement response
    """
    try:
        data = await request.json()
        logger.info(f"Received status update: {data}")
        
        # Just acknowledge receipt - no specific processing needed
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing status update: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/speech-update")
async def speech_update(request: Request):
    """
    Webhook endpoint for speech updates from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Acknowledgement response
    """
    try:
        data = await request.json()
        logger.info(f"Received speech update: {data}")
        
        # Just acknowledge receipt - no specific processing needed
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing speech update: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/conversation-update")
async def conversation_update(request: Request):
    """
    Webhook endpoint for conversation updates from Vapi.
    
    Args:
        request: The FastAPI request object
        
    Returns:
        dict: Acknowledgement response
    """
    try:
        data = await request.json()
        logger.info(f"Received conversation update: {data}")
        
        # Just acknowledge receipt - no specific processing needed
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error processing conversation update: {e}")
        # Always return success to prevent Vapi from retrying
        return {"status": "success"}

if __name__ == "__main__":
    logger.info(f"Starting Tofia Voice Assistant on {config.HOST}:{config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
