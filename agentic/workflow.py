"""
LangGraph workflow for the Agentic Health Assistant system.
Defines the graph structure and routing logic that connects the agents.
"""
import sys
import logging
import uuid
import os
from typing import Dict, List, Optional, Any, Union, Annotated, TypedDict
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

# Add parent directory to path to import from our own modules
sys.path.append('.')
sys.path.append('..')
sys.path.append(sys.path[0])
# Get current directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import directly from local modules
from schema import AgentState, IntentType, ConversationMemory, UserProfile
from agents.user_engagement_agent import UserEngagementAgent
from agents.task_planning_agent import TaskPlanningAgent
from agents.task_execution_agent import TaskExecutionAgent
from agents.final_agent import FinalAgent

logger = logging.getLogger(__name__)

def create_health_assistant_graph() -> StateGraph:
    """
    Create the LangGraph workflow for the health assistant.
    
    Returns:
        StateGraph: The configured workflow graph
    """
    # Initialize agents
    user_engagement_agent = UserEngagementAgent()
    task_planning_agent = TaskPlanningAgent()
    task_execution_agent = TaskExecutionAgent()
    final_agent = FinalAgent()
    
    # Create the graph
    workflow = StateGraph(AgentState)
    
    # Define the nodes in the graph
    workflow.add_node("user_engagement", user_engagement_agent)
    workflow.add_node("task_planning", task_planning_agent)
    workflow.add_node("task_execution", task_execution_agent)
    workflow.add_node("final", final_agent)
    
    # Define entry point - always start with user engagement
    workflow.set_entry_point("user_engagement")
    
    # Define edges between nodes based on intent and state
    
    # From user engagement node
    workflow.add_conditional_edges(
        "user_engagement",
        # Routing function to determine next node
        lambda state: _route_from_user_engagement(state),
        {
            "task_planning": "task_planning",
            "final": "final",
            "end": END
        }
    )
    
    # From task planning node
    workflow.add_edge("task_planning", "task_execution")
    
    # From task execution node
    workflow.add_conditional_edges(
        "task_execution",
        # Routing function to determine next node
        lambda state: _route_from_task_execution(state),
        {
            "task_execution": "task_execution",  # Loop back for multi-step execution
            "final": "final"
        }
    )
    
    # From final node, always end
    workflow.add_edge("final", END)
    
    # Compile the graph
    return workflow.compile()


def _route_from_user_engagement(state: AgentState) -> str:
    """
    Determine the next node after user engagement.
    
    Args:
        state: The current state
        
    Returns:
        str: The next node name
    """
    # Handle emergency intents immediately - these go to the final node
    if state.current_intent == IntentType.EMERGENCY:
        logger.warning("EMERGENCY intent detected - routing directly to final node")
        return "final"
    
    # Handle general info intents - may not need task planning
    if state.current_intent == IntentType.GENERAL_INFO:
        # For simple info requests, go directly to final
        if _is_simple_info_request(state):
            return "final"
    
    # Default path to task planning for most intents
    return "task_planning"


def _route_from_task_execution(state: AgentState) -> str:
    """
    Determine the next node after task execution.
    
    Args:
        state: The current state
        
    Returns:
        str: The next node name
    """
    # If task is still in progress, continue execution
    if state.task_plan and state.task_plan.status == "in_progress":
        return "task_execution"
    
    # Otherwise, move to final node
    return "final"


def _is_simple_info_request(state: AgentState) -> bool:
    """
    Determine if this is a simple information request that doesn't need planning.
    
    Args:
        state: The current state
        
    Returns:
        bool: True if this is a simple request
    """
    # Get the last user message
    if not state.memory.conversation_history:
        return False
        
    user_messages = [m for m in state.memory.conversation_history if m["role"] == "user"]
    if not user_messages:
        return False
        
    last_user_message = user_messages[-1]["content"].lower()
    
    # Check for simple health questions
    simple_question_markers = [
        "what is", "how do", "how can", "tell me about", 
        "when should", "definition of", "meaning of"
    ]
    
    # If the message is short and contains simple question markers
    is_short = len(last_user_message.split()) < 20
    has_marker = any(marker in last_user_message for marker in simple_question_markers)
    
    return is_short and has_marker


def initialize_agent_state(phone_number: str, user_input: str) -> AgentState:
    """
    Initialize a new agent state for a conversation.
    
    Args:
        phone_number: The user's phone number
        user_input: The initial user input
        
    Returns:
        AgentState: Initialized state
    """
    # Create a conversation ID
    conversation_id = f"conv-{uuid.uuid4().hex[:8]}"
    
    # Create initial user profile with phone number
    user_profile = UserProfile(phone_number=phone_number)
    
    # Create conversation memory
    memory = ConversationMemory(
        conversation_id=conversation_id,
        user_profile=user_profile,
        conversation_history=[]
    )
    
    # Create initial state
    return AgentState(
        memory=memory,
        user_input=user_input,
        current_agent=None,
        current_intent=None
    )
