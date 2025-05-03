"""
Flask server for the Agentic Health Assistant.
Provides API endpoints for integration with external systems like Vapi.
"""
import sys
import logging
import json
import argparse
from flask import Flask, request, jsonify, url_for
from typing import Dict, Any

# Add parent directory to path to import from our own modules
sys.path.append('.')
sys.path.append('..')
sys.path.append(sys.path[0])
import os
# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import directly from local modules instead of as a package
from health_assistant import health_assistant, handle_vapi_webhook

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint."""
    return jsonify({
        "service": "agentic-health-assistant",
        "description": "API for LangGraph-based health assistant system",
        "endpoints": [
            {"path": "/health", "method": "GET", "description": "Health check endpoint"},
            {"path": "/test", "method": "POST", "description": "Test the assistant with a message"},
            {"path": "/call", "method": "POST", "description": "Initiate an outbound call"},
            {"path": "/webhook/vapi", "method": "POST", "description": "Handle Vapi.ai webhooks"},
            {"path": "/routes", "method": "GET", "description": "View all available routes"}
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "service": "agentic-health-assistant",
        "status": "healthy"
    })

@app.route('/routes', methods=['GET'])
def list_routes():
    """List all available routes for debugging."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            "endpoint": rule.endpoint,
            "methods": [m for m in rule.methods if m not in ['HEAD', 'OPTIONS']],
            "path": str(rule)
        })
    return jsonify({"routes": routes})

@app.route('/webhook/vapi', methods=['POST'])
def vapi_webhook():
    """Handle Vapi.ai webhook requests."""
    try:
        request_data = request.json
        logger.info(f"Received webhook from Vapi: {request_data}")
        
        response = handle_vapi_webhook(request_data)
        logger.info(f"Sending response to Vapi: {response}")
        
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({
            "error": str(e),
            "action": "hangup"
        }), 500

@app.route('/call', methods=['POST'])
def outbound_call():
    """Initiate an outbound call."""
    try:
        request_data = request.json
        phone_number = request_data.get('phone_number')
        context = request_data.get('context', {})
        
        if not phone_number:
            return jsonify({"error": "phone_number is required"}), 400
            
        result = health_assistant.place_outbound_call(phone_number, context)
        
        if result:
            return jsonify({
                "success": True,
                "call_id": result.get("call_id"),
                "status": result.get("status")
            })
        else:
            return jsonify({"error": "Failed to place call"}), 500
    except Exception as e:
        logger.error(f"Error placing outbound call: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test', methods=['POST'])
def test_conversation():
    """Test endpoint for simulating a conversation without a phone call."""
    try:
        # Get parameters
        request_data = request.json
        phone_number = request_data.get('phone_number', '+11234567890')
        message = request_data.get('message', '')
        
        if not message:
            return jsonify({"error": "message is required"}), 400
            
        logger.info(f"Test conversation from {phone_number}: '{message}'")
        
        # Simulate a call
        mock_call_data = {
            "call_id": f"test-{phone_number}",
            "from": phone_number,
            "input": message
        }
        
        response = health_assistant.process_inbound_call(mock_call_data)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error in test conversation: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run the Agentic Health Assistant server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the server on')
    parser.add_argument('--host', default='0.0.0.0', help='Host to run the server on')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    
    args = parser.parse_args()
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Available routes: {[rule.rule for rule in app.url_map.iter_rules()]}")
    
    # Run the server
    app.run(host=args.host, port=args.port, debug=args.debug)
