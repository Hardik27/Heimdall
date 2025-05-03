"""
Configuration module for Tofia Voice Assistant.
Centralized location for all environment-specific settings.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Credentials
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "your_openai_api_key")
VAPI_API_KEY = os.getenv("VAPI_API_KEY", "your_vapi_api_key")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "your_twilio_sid")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "your_twilio_token")

# Phone Numbers
TOFIA_PHONE_NUMBER = os.getenv("TOFIA_PHONE_NUMBER", "+15551234567")
HOSPITAL_PHONE_NUMBER = os.getenv("HOSPITAL_PHONE_NUMBER", "+15559876543")

# GPT Model Configuration
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1000"))
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.7"))

# Database Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tofia.db")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Webhook URLs
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL", f"http://{HOST}:{PORT}")
INBOUND_CALL_WEBHOOK = f"{WEBHOOK_BASE_URL}/api/incoming_call"
CALL_STATUS_WEBHOOK = f"{WEBHOOK_BASE_URL}/api/call_status"

# SMS Templates
APPOINTMENT_CONFIRMATION_TEMPLATE = """
Hi {patient_name}, your appointment has been scheduled with {doctor_name} on {appointment_date} at {appointment_time}. 
Please arrive 15 minutes early. Reply YES to confirm or call us for any changes.
- Tofia Health Assistant
"""
