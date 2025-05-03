# Agentic Health Assistant

A LangGraph-based multi-agent system for health assistance and appointment scheduling. This system transforms the existing non-agentic codebase into a fully agentic architecture.

## Architecture Overview

The system is designed as a multi-agent workflow using LangGraph:

```
╭───────────────────────────────────╮             ╭────────────────────────────────╮
│ User Engagement & Memory Agent    │             │ Task Planning Agent            │
│ ----------------------------- │             │ --------------------- │
│ • Entry point of system           │             │ • Determines appropriate actions │
│ • Handles conversation & empathy  │────────────▶│ • Plans steps & workflows       │
│ • Manages memory & retrieval      │             │ • Resource discovery & routing  │
│ • Categorizes user intent         │◀────────────│ • Context tracking              │
╰───────────────────────────────────╯             ╰────────────────────────────────╯
                ▲                                                 │
                │                                                 ▼
                │                                  ╭────────────────────────────────╮
╭───────────────────────────────────╮             │ Task Execution Agent           │
│ Final Agent                       │             │ --------------------- │
│ -----------                       │◀────────────│ • Makes outbound calls/contacts │
│ • Ensures proper task closure     │             │ • Gathers provider responses    │
│ • Summarizes actions & outcomes   │             │ • Commits data to storage       │
│ • Handles follow-ups              │             │ • Finalizes appointments/tasks  │
╰───────────────────────────────────╯             ╰────────────────────────────────╯
```

## Components

1. **User Engagement & Memory Agent**: Initial agent that engages with the user, retrieves history, and categorizes intent.
   - Checks if the user exists in the database
   - Collects and stores basic information for new users
   - Personalizes the experience using past interaction history
   - Categorizes user intent

2. **Task Planning Agent**: Creates structured plans based on user intent.
   - Understands context and requirements
   - Determines which services are appropriate
   - Creates step-by-step plans for task execution

3. **Task Execution Agent**: Executes plans and interacts with external systems.
   - Makes outbound calls to healthcare providers
   - Gathers responses and relevant data
   - Selects options based on user preferences
   - Finalizes appointments

4. **Final Agent**: Ensures proper closure of tasks.
   - Summarizes completed actions
   - Confirms outcomes with the user
   - Provides a human-like closure to interactions

## Memory Architecture

The system maintains memory at three levels:

1. **Conversation Memory**: Short-term memory of the current conversation.
   - Maintained in the `ConversationMemory` object
   - Passed between agents in the workflow

2. **User Profile Storage**: Long-term memory of user information.
   - Stored in the database via the existing `MemoryStore`
   - Includes personal details, preferences, medical history

3. **Interaction History**: Record of past calls and appointments.
   - Stored in the `CallRecord` table
   - Used to personalize future interactions

## Integration Points

- **Vapi Integration**: For handling inbound and outbound calls.
- **Database Integration**: Using the existing SQLAlchemy models.
- **SMS Notifications**: For appointment confirmations via the existing SMS module.

## Gradual Rollout Strategy

The integration layer allows for a gradual rollout of the agentic system:

- Feature flag controls global system activation
- Percentage-based rollout based on phone number hash
- User-specific opt-in/opt-out capabilities

## Setup and Installation

1. Install the required packages:
   ```
   pip install -r agentic/requirements.txt
   ```

2. Configure the environment:
   - Set OpenAI API key in the `config.py` file
   - Configure Vapi settings
   - Set database connection details

3. Start the server:
   ```
   python agentic/server.py
   ```

## Testing

Test the system using the built-in test endpoint:
```
curl -X POST http://localhost:5000/api/test-conversation \
   -H "Content-Type: application/json" \
   -d '{"phone_number": "+12345678901", "message": "I need to schedule a doctor appointment"}'
```

## Integration with Existing System

The system can run alongside the existing non-agentic codebase, with the integration module handling routing between them. This allows for:

- A/B testing between systems
- Gradual rollout to users
- Fallback to the original system if needed
