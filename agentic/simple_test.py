"""
Simple test script for the Agentic Health Assistant.
Uses direct imports to test the core components.
"""
import sys
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the schema directly
from schema import IntentType, UserProfile, ConversationMemory, AgentState
from prompts import USER_ENGAGEMENT_AGENT_PROMPT

def test_schema():
    """Test the schema definitions."""
    print("Testing schema definitions...")
    print("-" * 80)
    
    # Create a conversation ID
    conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
    
    # Create a user profile
    user_profile = UserProfile(
        phone_number="+1234567890",
        name="Test User",
        date_of_birth="1980-01-01",
        insurance_provider="Test Insurance"
    )
    
    # Create conversation memory
    memory = ConversationMemory(
        conversation_id=conversation_id,
        user_profile=user_profile,
        conversation_history=[
            {"role": "user", "content": "I need to schedule a doctor appointment"}
        ]
    )
    
    # Create a state
    state = AgentState(
        memory=memory,
        user_input="I need to schedule a doctor appointment",
        current_intent=IntentType.APPOINTMENT_SCHEDULING
    )
    
    # Print the created objects
    print(f"Conversation ID: {conversation_id}")
    print(f"User Profile: {user_profile.phone_number} - {user_profile.name}")
    print(f"Intent: {state.current_intent}")
    print("-" * 80)
    
    return state

def test_llm():
    """Test LLM integration with a simple prompt."""
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        import os
        
        print("Testing LLM integration...")
        print("-" * 80)
        
        # Check for OpenAI API key
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("⚠️ No OPENAI_API_KEY found in environment variables.")
            print("Please set your OpenAI API key to test LLM integration.")
            print("Example: export OPENAI_API_KEY=your-key-here")
            print("-" * 80)
            return False
        
        # Create a simple LLM
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7
        )
        
        # Test with a simple prompt
        messages = [
            HumanMessage(content="You are a health assistant. Respond to this request: I need to see a doctor for a persistent cough.")
        ]
        
        response = llm.invoke(messages)
        
        print("LLM Response:")
        print(response.content)
        print("-" * 80)
        
        return True
    except Exception as e:
        print(f"Error testing LLM: {e}")
        print("-" * 80)
        return False

def main():
    """Run the simple test."""
    print("Running simple test for Agentic Health Assistant...")
    
    # Test schema
    state = test_schema()
    
    # Test LLM integration
    llm_success = test_llm()
    
    if llm_success:
        print("All tests completed successfully!")
    else:
        print("Tests completed with some issues. See above for details.")
    
    return state

if __name__ == "__main__":
    main()
