"""
Base agent definition for the Agentic Health Assistant system.
"""
import sys
import logging
import os
from typing import Dict, List, Optional, Any, Union, Callable
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from dotenv import load_dotenv

# Get the absolute path to the .env file in the agentic directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)  # agentic directory
env_path = os.path.join(parent_dir, '.env')

# Load environment variables from the specific .env file
load_dotenv(dotenv_path=env_path)
logger = logging.getLogger(__name__)
logger.info(f"Loading environment from: {env_path}")
logger.info(f"OPENAI_API_KEY: {os.environ.get('OPENAI_API_KEY', '')[:4]}***")

# Add parent directory to path to import from our own modules
sys.path.append('..')
sys.path.append('../..')
# Import directly from local modules
from schema import AgentState
import config

class BaseAgent:
    """Base class for all agents in the Agentic Health Assistant system."""
    
    def __init__(self, system_prompt: str, model_name: Optional[str] = None):
        """
        Initialize the base agent.
        
        Args:
            system_prompt: The system prompt for this agent
            model_name: Optional model name to override the default
        """
        self.system_prompt = system_prompt
        self.model_name = model_name or os.environ.get('GPT_MODEL', 'gpt-4-0125-preview')
        
        # Get API key directly from environment 
        api_key = os.environ.get('OPENAI_API_KEY')
        
        # Log API key information (first 4 chars only, for debugging)
        if api_key and len(api_key) > 8:
            logger.info(f"Using API key starting with: {api_key[:4]}***")
        else:
            logger.error(f"Invalid OpenAI API key found: {api_key if api_key else 'None'}")
            
        # Initialize the language model
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0.7,
            api_key=api_key
        )
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
    
    def extract_conversation_history(self, state: AgentState) -> List[Union[HumanMessage, AIMessage]]:
        """
        Extract conversation history from state in a format suitable for the LLM.
        
        Args:
            state: The current agent state
            
        Returns:
            List of message objects
        """
        messages = []
        
        # Convert conversation history to LangChain message format
        for msg in state.memory.conversation_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        return messages
    
    def __call__(self, state: AgentState) -> AgentState:
        """
        Process the current state and generate a response.
        
        Args:
            state: The current state from the LangGraph
            
        Returns:
            Updated state
        """
        try:
            # Set the agent identifier
            state.current_agent = self.__class__.__name__
            
            # Extract conversation history
            history = self.extract_conversation_history(state)
            
            # Get the user input
            user_input = state.user_input or "Hello"
            
            # Process through LLM
            chain = self.prompt | self.llm
            response = chain.invoke({
                "history": history,
                "input": user_input
            })
            
            # Extract the response content
            response_content = response.content
            
            # Update the state with the response
            state.response_to_user = response_content
            
            # Add to conversation history
            state.memory.conversation_history.append({
                "role": "user",
                "content": user_input
            })
            state.memory.conversation_history.append({
                "role": "assistant",
                "content": response_content
            })
            
            # Store the current agent state
            state.memory.last_agent_state = self.__class__.__name__
            
            return state
        except Exception as e:
            logger.error(f"Error in agent {self.__class__.__name__}: {e}")
            state.error = f"Error in {self.__class__.__name__}: {str(e)}"
            return state
