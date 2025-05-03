You are an expert Python engineer building a voice-assistant backend for healthcare. Follow these requirements carefully:

**Overview:** We are implementing "Tofia", an AI voice assistant for medical appointment scheduling. The system receives inbound calls from patients and makes outbound calls to hospital receptionists using Vapi.ai (a voice AI telephony platform). It also sends SMS confirmations via Twilio. The backend must be HIPAA-compliant, modular, and extensible.

**Key Features to Implement:**

1. **Telephony Handler (using Vapi SDK):**

   - Handle inbound calls: When a call comes in on a Vapi number, use a webhook endpoint to process it. Identify the caller by phone number.
   - For inbound calls, start a conversation with the patient via the AI assistant.
   - Handle outbound calls: Use Vapi’s API/SDK to place calls to hospitals. Provide a separate AI assistant persona for these calls.
   - Ensure the telephony module can receive events or transcripts from Vapi in real-time or after call completion.
   - After an outbound call, capture the outcome (e.g., confirmed appointment details).

2. **Conversation Agents (GPT-4 Integration):**

   - **PatientAgent:** Manages dialogue with the patient. Use OpenAI GPT-4 to generate responses. Prompt it with a friendly, empathetic tone. It should gather intent (e.g., scheduling) and required info (name, DOB, insurance) if not already known.
   - **HospitalAgent:** Manages dialogue with the receptionist. Also use GPT-4, but with a professional tone and all necessary patient info in the prompt. This agent should explicitly ask to book an appointment and respond to the receptionist’s queries.
   - Use OpenAI’s Python API (openai package) to send messages to GPT-4. Structure the prompts with system and user messages as described.
   - Ensure the ability to handle multi-turn conversation. (Hint: maintain `conversation_history` for each call and append new messages).

3. **Memory Module (Database Persistence):**

   - Use a simple database (SQLite or PostgreSQL via an ORM) to store caller profiles and call history.
   - Schema: a `Caller` table (phone number as ID, name, etc.) and a `CallRecord` table (timestamp, caller_id, summary, maybe type of call).
   - On an incoming call, lookup the Caller by phone. If not found, create a new record (first-time caller).
   - Store key details from each call: e.g., the patient’s provided info and the appointment scheduled.
   - Provide functions like `get_caller(phone)` and `save_call_record(caller, summary)`.

4. **SMS Notification (Twilio API):**

   - After successfully scheduling an appointment, use Twilio’s REST API (twilioClient) to send an SMS to the patient’s number with confirmation details.
   - Make the SMS content clear and HIPAA-compliant (no overly sensitive info).

5. **Orchestration Logic:**
   - Tie everything together in a `VoiceAssistant` class or similar.
   - Inbound call flow: trigger PatientAgent; when PatientAgent determines an appointment needs scheduling (intent identified and info collected), end the patient call gracefully.
   - Then invoke HospitalAgent via an outbound Vapi call. (Option: you can simulate the conversation for now by calling HospitalAgent’s response generator in a loop with sample receptionist prompts, since fully integrating real phone for tests is hard).
   - Once appointment info is obtained, send SMS to patient and store the call records in the DB.
   - Ensure to log or print key steps for traceability (e.g., “Patient called, identified intent = schedule_appointment”, “Calling hospital…”, “Appointment confirmed”).
   - Make sure each step handles errors: e.g., if GPT-4 API fails, handle exception and maybe retry or default a response; if Twilio SMS fails, log error.

**Technical Requirements:**

- Use Python 3.10+ with `fastapi` (for webhooks) or an equivalent lightweight HTTP server to receive Vapi webhooks for inbound calls and call status.
- Use `pydantic` models or dataclasses for data structures (like Call data) where appropriate.
- Use an ORM like `sqlalchemy` or Django ORM (if using Django) for the database, or even a simple dictionary for in-memory simulation (but structure code so it’s easy to swap in a real DB).
- The code should be modular: define classes for each major component (TelephonyHandler, PatientAgent, HospitalAgent, MemoryStore, etc.). Each class should have clear methods as interface.
- Write docstrings for classes and methods explaining their purpose, and inline comments for complex logic.
- Maintain separation of concerns: e.g., the PatientAgent class shouldn’t directly access Twilio or DB – it should return info to the orchestrator which then calls the Memory or SMS modules.
- Ensure compliance: do not print or log sensitive data (like full PHI) – if logging, redact or log high-level events only.

**Structure:**
You may produce multiple Python files or one file with sections. For simplicity, you can put everything in one `tofia_backend.py` file, but use distinct classes as described. Organize the code as:

- imports
- global configs (API keys, etc., which you can leave as placeholders)
- database setup (for example, SQLAlchemy models or a simple in-memory dict)
- class definitions (MemoryStore, PatientAgent, HospitalAgent, TelephonyHandler, VoiceAssistant, etc.)
- if using FastAPI, define the webhook endpoints (e.g., `/incoming_call` for Vapi to post to)
- main block to run the FastAPI app (if applicable).

Given the complexity, you can mock certain interactions for now (for example, instead of making an actual outbound call in HospitalAgent, just simulate the conversation with predefined questions). Focus on showing the flow and module interactions.

Now, **write the complete Python code** implementing the above. Make sure the code is clean, well-organized, and commented.
