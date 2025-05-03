"""
Mock test for the agentic health assistant that demonstrates the multi-agent architecture.
This script simulates the workflow without making any actual OpenAI API calls.
"""
import os
import sys
import logging
import uuid
import json
from datetime import datetime
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock data
MOCK_RESPONSES = {
    "appointment_scheduling": {
        "user_engagement": "I understand you'd like to schedule a doctor appointment for your back pain. I can help with that. Let me get some information from you first.",
        "task_planning": [
            {"step_number": 1, "description": "Gather patient information"},
            {"step_number": 2, "description": "Check doctor availability at preferred hospital"},
            {"step_number": 3, "description": "Book appointment with appropriate specialist"},
            {"step_number": 4, "description": "Send confirmation to patient"}
        ],
        "task_execution": {
            "outbound_call": {
                "action": "outbound_call",
                "target": "hospital",
                "status": "successful",
                "appointment": {
                    "doctor_name": "Dr. Sarah Johnson",
                    "specialty": "Orthopedics",
                    "date": "2025-05-10",
                    "time": "2:30 PM",
                    "facility": "General Hospital",
                    "address": "123 Medical Center Drive"
                }
            }
        },
        "final_response": "Great news! I've scheduled an appointment for your back pain with Dr. Sarah Johnson, who specializes in Orthopedics. Your appointment is set for Saturday, May 10th at 2:30 PM at General Hospital (123 Medical Center Drive). I've also sent you a confirmation SMS with these details. Is there anything else you'd like to know about your appointment?"
    },
    "medical_advice_headache": {
        "user_engagement": "I understand you're experiencing severe headaches and looking for advice. While I can provide general information, please consult a healthcare professional for specific medical advice, especially for severe or persistent symptoms.",
        "task_planning": [
            {"step_number": 1, "description": "Identify specific headache symptoms and characteristics"},
            {"step_number": 2, "description": "Research relevant medical information about headaches"},
            {"step_number": 3, "description": "Provide general guidance based on symptoms"},
            {"step_number": 4, "description": "Recommend professional consultation given severity"}
        ],
        "task_execution": {
            "information_lookup": {
                "action": "information_lookup",
                "source": "medical_database",
                "status": "successful",
                "information": "Severe headaches lasting for a week could indicate several conditions including migraines, tension headaches, cluster headaches, or secondary headaches due to underlying conditions. Persistent severe headaches warrant medical evaluation."
            }
        },
        "final_response": "Based on the information you've shared about experiencing severe headaches for a week, this could potentially be migraines, tension headaches, or another type of headache disorder. However, headaches that are severe and persistent for this duration should be evaluated by a healthcare provider. Common self-care approaches include rest in a dark, quiet room, staying hydrated, and over-the-counter pain medications, but given the severity and duration, I strongly recommend scheduling an appointment with a doctor for proper diagnosis. Would you like me to help arrange an appointment with a neurologist who specializes in headaches?"
    },
    "medical_advice_back_pain": {
        "user_engagement": "I understand you're experiencing back pain and looking for advice. While I can provide general information, please consult a healthcare professional for specific medical advice.",
        "task_planning": [
            {"step_number": 1, "description": "Identify specific back pain characteristics"},
            {"step_number": 2, "description": "Research relevant medical information"},
            {"step_number": 3, "description": "Provide general guidance"},
            {"step_number": 4, "description": "Recommend professional consultation if needed"}
        ],
        "task_execution": {
            "information_lookup": {
                "action": "information_lookup",
                "source": "medical_database",
                "status": "successful",
                "information": "Back pain can be caused by muscle or ligament strain, bulging or ruptured disks, arthritis, or skeletal irregularities. Most back pain gradually improves with home treatment and self-care."
            }
        },
        "final_response": "Based on the information you've provided about your back pain, this could be related to muscle strain, which is common and often improves with rest and over-the-counter pain relievers. However, since you've mentioned it's persistent, I would recommend seeing a doctor for proper diagnosis. Would you like me to help schedule an appointment with a specialist?"
    }
}

class MockState:
    """Simulated state object that mimics the real AgentState."""
    
    def __init__(self, user_input, phone_number):
        self.user_input = user_input
        self.conversation_id = str(uuid.uuid4())
        self.current_intent = None
        self.response_to_user = None
        self.task_plan = None
        self.completed = False
        self.memory = {
            "user_profile": {
                "phone_number": phone_number,
                "name": "Test User",
                "date_of_birth": "1980-01-01"
            },
            "conversation_history": [
                {"role": "user", "content": user_input, "timestamp": datetime.now().isoformat()}
            ]
        }

class MockUserEngagementAgent:
    """Mock implementation of the User Engagement Agent."""
    
    def __call__(self, state):
        logger.info("🧠 USER ENGAGEMENT AGENT: Processing user input...")
        
        # Detect intent from input
        user_input_lower = state.user_input.lower()
        
        if "appointment" in user_input_lower or "schedule" in user_input_lower:
            state.current_intent = "appointment_scheduling"
            response = MOCK_RESPONSES["appointment_scheduling"]["user_engagement"]
        elif "headache" in user_input_lower or "migraine" in user_input_lower:
            state.current_intent = "medical_advice_headache"
            response = MOCK_RESPONSES["medical_advice_headache"]["user_engagement"]
        elif "back pain" in user_input_lower or "backache" in user_input_lower:
            state.current_intent = "medical_advice_back_pain"
            response = MOCK_RESPONSES["medical_advice_back_pain"]["user_engagement"]
        elif "advice" in user_input_lower or "pain" in user_input_lower:
            # General medical advice query
            state.current_intent = "medical_advice_general"
            response = "I understand you're looking for medical advice. While I can provide general information, I recommend consulting a healthcare professional for specific diagnoses and treatments."
        else:
            state.current_intent = "general_info"
            response = "I understand you need assistance. How can I help you today?"
        
        logger.info(f"✅ Detected intent: {state.current_intent}")
        logger.info(f"✅ Response: {response}")
        
        state.response_to_user = response
        return state

class MockTaskPlanningAgent:
    """Mock implementation of the Task Planning Agent."""
    
    def __call__(self, state):
        logger.info("📝 TASK PLANNING AGENT: Creating task plan...")
        
        # Get task plan based on intent
        if state.current_intent == "appointment_scheduling":
            steps = MOCK_RESPONSES["appointment_scheduling"]["task_planning"]
        elif state.current_intent == "medical_advice_headache":
            steps = MOCK_RESPONSES["medical_advice_headache"]["task_planning"]
        elif state.current_intent == "medical_advice_back_pain":
            steps = MOCK_RESPONSES["medical_advice_back_pain"]["task_planning"]
        else:
            steps = [
                {"step_number": 1, "description": "Understand user request"},
                {"step_number": 2, "description": "Provide relevant information"}
            ]
        
        # Create task plan
        state.task_plan = {
            "task_id": str(uuid.uuid4()),
            "task_type": state.current_intent,
            "steps": steps,
            "status": "created",
            "current_step_index": 0
        }
        
        logger.info(f"✅ Created task plan with {len(steps)} steps")
        for step in steps:
            logger.info(f"   - Step {step['step_number']}: {step['description']}")
        
        return state

class MockTaskExecutionAgent:
    """Mock implementation of the Task Execution Agent."""
    
    def __call__(self, state):
        logger.info("🔧 TASK EXECUTION AGENT: Executing task plan...")
        
        # Get execution result based on intent
        if state.current_intent == "appointment_scheduling":
            execution_result = MOCK_RESPONSES["appointment_scheduling"]["task_execution"]
            state.appointment_details = execution_result["outbound_call"]["appointment"]
        elif state.current_intent == "medical_advice_headache":
            execution_result = MOCK_RESPONSES["medical_advice_headache"]["task_execution"]
        elif state.current_intent == "medical_advice_back_pain":
            execution_result = MOCK_RESPONSES["medical_advice_back_pain"]["task_execution"]
        else:
            execution_result = {
                "action": "information_retrieval",
                "status": "completed",
                "information": "General health information retrieved successfully."
            }
        
        # Update task plan status
        state.task_plan["status"] = "completed"
        state.task_plan["current_step_index"] = len(state.task_plan["steps"])
        
        logger.info(f"✅ Execution complete: {json.dumps(execution_result, indent=2)}")
        
        return state

class MockFinalAgent:
    """Mock implementation of the Final Agent."""
    
    def __call__(self, state):
        logger.info("🎬 FINAL AGENT: Providing closure to conversation...")
        
        # Get final response based on intent
        if state.current_intent == "appointment_scheduling":
            final_response = MOCK_RESPONSES["appointment_scheduling"]["final_response"]
        elif state.current_intent == "medical_advice_headache":
            final_response = MOCK_RESPONSES["medical_advice_headache"]["final_response"]
        elif state.current_intent == "medical_advice_back_pain":
            final_response = MOCK_RESPONSES["medical_advice_back_pain"]["final_response"]
        else:
            final_response = "Thank you for your inquiry. I hope I was able to assist you today. Is there anything else you need help with?"
        
        state.response_to_user = final_response
        state.completed = True
        
        logger.info(f"✅ Final response: {final_response}")
        
        return state

def run_mock_workflow(user_message, phone_number="+15551234567"):
    """Run the mock workflow to demonstrate the multi-agent architecture."""
    
    logger.info("=" * 80)
    logger.info(f"STARTING WORKFLOW: Input message = '{user_message}'")
    logger.info("=" * 80)
    
    # Initialize the agents
    user_engagement_agent = MockUserEngagementAgent()
    task_planning_agent = MockTaskPlanningAgent()
    task_execution_agent = MockTaskExecutionAgent()
    final_agent = MockFinalAgent()
    
    # Initialize state
    state = MockState(user_message, phone_number)
    
    # Step 1: User Engagement Agent (Intent detection, initial response)
    logger.info("\n\nSTEP 1: USER ENGAGEMENT AGENT")
    logger.info("-" * 80)
    state = user_engagement_agent(state)
    
    # Check if we need task planning or can directly respond
    if state.current_intent not in ["general_info"]:
        # Step 2: Task Planning Agent (Create structured plan)
        logger.info("\n\nSTEP 2: TASK PLANNING AGENT")
        logger.info("-" * 80)
        state = task_planning_agent(state)
        
        # Step 3: Task Execution Agent (Execute plan, interact with external systems)
        logger.info("\n\nSTEP 3: TASK EXECUTION AGENT")
        logger.info("-" * 80)
        state = task_execution_agent(state)
        
        # Step 4: Final Agent (Provide closure and summary)
        logger.info("\n\nSTEP 4: FINAL AGENT")
        logger.info("-" * 80)
        state = final_agent(state)
    else:
        # Simple query, skip to final response
        logger.info("\n\nSKIPPING COMPLEX WORKFLOW: Using direct response for simple query")
        logger.info("-" * 80)
        state.completed = True
    
    # Show final result
    logger.info("\n\n")
    logger.info("=" * 80)
    logger.info("WORKFLOW COMPLETE!")
    logger.info(f"Final response to user: {state.response_to_user}")
    logger.info("=" * 80)
    
    return state

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test the agentic health assistant with mock data")
    parser.add_argument("--message", default="I need to schedule a doctor appointment for my back pain", 
                      help="Test message to process")
    parser.add_argument("--phone", default="+15551234567", help="Test phone number")
    
    args = parser.parse_args()
    
    # Run the mock workflow
    run_mock_workflow(args.message, args.phone)
