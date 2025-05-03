"""
FastAPI application for Tofia Voice Assistant.
Implements webhook endpoints for Vapi.ai integration.
"""
import logging
import uvicorn
from fastapi import FastAPI, Request, HTTPException
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

# Create voice assistant instance
tofia = VoiceAssistant()

@app.get("/")
async def root():
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
        
        call_sid = data.get("call_sid")
        message = data.get("transcript", "")
        
        response = tofia.process_patient_message(call_sid, message)
        return response
    
    except Exception as e:
        logger.error(f"Error processing patient message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
        
        call_sid = data.get("call_sid")
        message = data.get("transcript", "")
        
        response = tofia.process_hospital_message(call_sid, message)
        return response
    
    except Exception as e:
        logger.error(f"Error processing hospital message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/call_status")
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

if __name__ == "__main__":
    logger.info(f"Starting Tofia Voice Assistant on {config.HOST}:{config.PORT}")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
