#!/usr/bin/env python3
"""
Deployment script for Tofia Voice Assistant using ngrok.
Starts the FastAPI server and ngrok tunnel, then updates configuration.
"""
import os
import sys
import time
import signal
import subprocess
import requests
import json
from dotenv import load_dotenv, set_key

# Configuration
FASTAPI_PORT = 8080
ENV_FILE = ".env"

def start_fastapi_server():
    """Start the FastAPI server as a background process."""
    print("Starting FastAPI server...")
    # Using uvicorn to run the FastAPI app
    fastapi_process = subprocess.Popen(
        ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", str(FASTAPI_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(3)  # Give it time to start
    return fastapi_process

def start_ngrok():
    """Start ngrok to expose the FastAPI server."""
    print("Starting ngrok tunnel...")
    # Start ngrok to expose the local server
    ngrok_process = subprocess.Popen(
        ["ngrok", "http", str(FASTAPI_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    time.sleep(2)  # Give it time to start
    
    # Get the ngrok URL
    try:
        response = requests.get("http://localhost:4040/api/tunnels")
        tunnels = json.loads(response.text)["tunnels"]
        if tunnels:
            ngrok_url = tunnels[0]["public_url"]
            print(f"Ngrok tunnel established at: {ngrok_url}")
            return ngrok_process, ngrok_url
        else:
            print("No ngrok tunnels found")
            return ngrok_process, None
    except Exception as e:
        print(f"Error getting ngrok URL: {e}")
        return ngrok_process, None

def update_environment(ngrok_url):
    """Update the .env file with the ngrok URL."""
    print(f"Updating environment with ngrok URL: {ngrok_url}")
    # Load the current .env file
    load_dotenv(ENV_FILE)
    
    # Update the WEBHOOK_BASE_URL
    set_key(ENV_FILE, "WEBHOOK_BASE_URL", ngrok_url)
    print("Environment updated successfully")

def signal_handler(sig, frame):
    """Handle Ctrl+C to terminate processes gracefully."""
    print("Shutting down...")
    if 'ngrok_process' in globals():
        ngrok_process.terminate()
    if 'fastapi_process' in globals():
        fastapi_process.terminate()
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    # Step 1: Start FastAPI server
    fastapi_process = start_fastapi_server()
    
    # Step 2: Start ngrok
    ngrok_process, ngrok_url = start_ngrok()
    
    if not ngrok_url:
        print("Failed to get ngrok URL. Please check if ngrok is properly installed.")
        fastapi_process.terminate()
        ngrok_process.terminate()
        sys.exit(1)
    
    # Step 3: Update environment
    update_environment(ngrok_url)
    
    # Step 4: Display deployment information
    print("\n" + "="*50)
    print("TOFIA VOICE ASSISTANT DEPLOYMENT")
    print("="*50)
    print(f"Local server: http://localhost:{FASTAPI_PORT}")
    print(f"Public URL: {ngrok_url}")
    print("\nYou can now configure Vapi to use the following webhook URLs:")
    print(f"Incoming call webhook: {ngrok_url}/api/incoming_call")
    print(f"Patient conversation webhook: {ngrok_url}/api/patient_conversation")
    print(f"Hospital conversation webhook: {ngrok_url}/api/hospital_conversation")
    print(f"Call status webhook: {ngrok_url}/api/call_status")
    print("\nAPI Documentation: {ngrok_url}/docs")
    print("="*50)
    print("\nPress Ctrl+C to stop the deployment")
    
    # Keep the script running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)
