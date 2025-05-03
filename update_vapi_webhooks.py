#!/usr/bin/env python3
"""
Script to update Vapi configuration to use custom webhooks.
This ensures Vapi uses your custom LLM agents instead of its built-in LLM.
"""
import requests
import os
from dotenv import load_dotenv
import json
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_PHONE_NUMBER_ID = os.getenv("VAPI_PHONE_NUMBER_ID")
WEBHOOK_BASE_URL = os.getenv("WEBHOOK_BASE_URL")

def list_phone_numbers():
    """List all phone numbers in the Vapi account."""
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        url = "https://api.vapi.ai/call/phone-numbers"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            numbers = response.json()
            logger.info(f"Found {len(numbers)} phone numbers")
            for i, number in enumerate(numbers):
                print(f"{i+1}. Number: {number.get('number')}, ID: {number.get('id')}")
            return numbers
        else:
            logger.error(f"Failed to list phone numbers: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error listing phone numbers: {e}")
        return []

def update_assistant_for_number(phone_number_id):
    """
    Update the phone number's server URL and disable the assistant.
    
    This function configures a phone number to use webhooks instead of Vapi's LLM.
    """
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Configuration data for the phone number
    data = {
        "serverUrl": WEBHOOK_BASE_URL,
        "webhookUrl": f"{WEBHOOK_BASE_URL}/api/incoming_call",
        "statusCallbackUrl": f"{WEBHOOK_BASE_URL}/api/call_status",
        "disableAssistant": True  # Explicitly disable Vapi's assistant
    }
    
    logger.info(f"Updating phone number {phone_number_id} with webhook URL {WEBHOOK_BASE_URL}")
    
    try:
        # Make the API request to update the phone number
        url = f"https://api.vapi.ai/call/phone-numbers/{phone_number_id}"
        response = requests.patch(url, headers=headers, json=data)
        
        if response.status_code in [200, 201, 204]:
            logger.info(f"Successfully updated phone number configuration")
            try:
                logger.info(f"Response: {json.dumps(response.json(), indent=2)}")
            except:
                logger.info(f"Response status code: {response.status_code}")
            return True
        else:
            logger.error(f"Failed to update phone number: {response.status_code}")
            logger.error(f"Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Error updating phone number configuration: {e}")
        return False

def create_outbound_call_config():
    """
    Create a new outbound call configuration.
    This demonstrates how to configure outbound calls to use your webhook.
    """
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Example phone number - you would replace this with the target number
    to_number = "+11234567890"  # Replace with your test number
    
    data = {
        "phoneNumberId": VAPI_PHONE_NUMBER_ID,
        "customer": {
            "number": to_number
        },
        "assistant": None,  # Explicitly set to None to disable Vapi's built-in assistant
        "functions": [
            {
                "name": "transfer_to_webhook",
                "description": "Transfer control to our custom webhook",
                "parameters": {}
            }
        ],
        "messages": [
            {
                "role": "system",
                "content": "Transferring to Tofia assistant..."
            }
        ],
        "webhook": {
            "url": f"{WEBHOOK_BASE_URL}/api/hospital_conversation"
        },
        "statusCallback": f"{WEBHOOK_BASE_URL}/api/call_status",
        "recording": {
            "enabled": True
        },
        "disableAssistant": True
    }
    
    logger.info(f"Creating example outbound call configuration")
    
    try:
        # Make the API request to create an example call
        url = "https://api.vapi.ai/call/phone"
        
        # Don't actually place the call, just print the configuration
        logger.info(f"Example outbound call configuration:")
        logger.info(json.dumps(data, indent=2))
        
        # Uncomment to make a real call:
        # response = requests.post(url, headers=headers, json=data)
        # if response.status_code == 200:
        #     call_data = response.json()
        #     logger.info(f"Call initiated: {call_data.get('id')}")
        # else:
        #     logger.error(f"Failed to place call: {response.status_code}")
        #     logger.error(f"Response: {response.text}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating call configuration: {e}")
        return False

if __name__ == "__main__":
    print("=======================================")
    print("Vapi Webhook Configuration Utility")
    print("=======================================")
    print(f"Using webhook base URL: {WEBHOOK_BASE_URL}")
    print("---------------------------------------")
    
    # List all phone numbers first
    print("\nListing available phone numbers:")
    numbers = list_phone_numbers()
    
    if numbers:
        # Ask user which phone number to update
        print("\nWhich phone number would you like to update?")
        choice = input("Enter the number (1, 2, etc.) or 'q' to quit: ")
        
        if choice.lower() != 'q' and choice.isdigit() and 1 <= int(choice) <= len(numbers):
            index = int(choice) - 1
            selected_number = numbers[index]
            phone_id = selected_number.get('id')
            
            print(f"\nSelected phone number: {selected_number.get('number')}")
            print(f"Phone ID: {phone_id}")
            
            update = input("Do you want to update this phone number to use your webhooks? (y/n): ")
            if update.lower() == 'y':
                success = update_assistant_for_number(phone_id)
                if success:
                    print("\nPhone number configuration updated successfully!")
                    print("\nExample outbound call configuration:")
                    create_outbound_call_config()
                else:
                    print("\nFailed to update phone number configuration.")
            else:
                print("\nConfiguration update cancelled.")
        else:
            print("\nInvalid selection or cancelled.")
    else:
        print("\nNo phone numbers found or error retrieving phone numbers.")
