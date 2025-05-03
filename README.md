# Tofia 📞 — Two‑Agent Voice Appointment Scheduler

Tofia is a FastAPI application that:

1. **Collects six pieces of patient info** in a strict order  
   *full name → date of birth → insurance provider → member ID → ZIP → symptoms*  
2. Stores the data in SQLite (or PostgreSQL) via SQLAlchemy  
3. Spawns a second VAPI assistant (**Riley**) to call the hospital and book the earliest appointment  
4. Sends an SMS confirmation (Twilio) when the appointment is secured

## 📁 Repository Layout

| Path                     | Purpose                                                      |
|--------------------------|--------------------------------------------------------------|
| `app.py`                | FastAPI entry + webhook routes                               |
| `voice_assistant.py`    | Session stepper & hospital-call trigger                      |
| `conversation_agents.py`| GPT helpers (still optional)                                 |
| `telephony_handler.py`  | Outbound VAPI REST calls                                     |
| `memory_module.py`      | DB helpers                                                   |
| `models.py`             | SQLAlchemy ORM (`Caller`, `CallRecord`, `Hospital`)          |
| `sms_notifications.py`  | Twilio wrapper (optional)                                    |
| `update_vapi_webhooks.py`| Script to PATCH VAPI assistants to `custom_server` mode     |
| `.env.example`          | Template environment config                                  |

---

## 🔐 `.env` Template

```dotenv
### FastAPI ###
HOST=0.0.0.0
PORT=8000

### Database ###
DATABASE_URL=sqlite:///tofia.db
# Or: postgresql://user:pass@host:5432/tofia

### VAPI ###
VAPI_API_KEY=sk_********************************<
PATIENT_ASSISTANT_ID=<assistant_id>   # Tofia
HOSPITAL_ASSISTANT_ID=<hospital_assistant_id>  # Riley
VAPI_PHONE_NUMBER_ID=<vapi_phone_number_id>   # your FROM #
HOSPITAL_PHONE_NUMBER=+1<enter-10-digit phone number>                        # hospital desk

### OpenAI (optional GPT) ###
OPENAI_API_KEY=sk-********************************
GPT_MODEL=gpt-4o
MAX_TOKENS=800
TEMPERATURE=0.7

### ngrok ###
WEBHOOK_BASE_URL=https://xxxx-xx-xx-xxx.ngrok-free.app

### Twilio (SMS, optional) ###
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TOFIA_PHONE_NUMBER=<PATIENT_ASSISTANT_PHONE_NUMBER>



## ⚙️ Local Setup (Python 3.10+)

```bash
git clone https://github.com/your-org/tofia.git
cd tofia
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt


---

## Workflow

```mermaid
flowchart TD
    Caller((Patient<br/>Phone))
    VAPI_Tofia["Tofia<br/>(Patient Agent)"]
    FastAPI["FastAPI<br/>App + DB"]
    Telephony["TelephonyHandler<br/>place_outbound_call"]
    VAPI_Riley["Riley<br/>(Hospital Agent)"]
    Hospital((Hospital<br/>Reception))
    Twilio["Twilio<br/>SMS"]

    Caller -->|dials| VAPI_Tofia
    VAPI_Tofia -- "POST /api/incoming_call" --> FastAPI
    FastAPI -- "Question 1" --> VAPI_Tofia
    VAPI_Tofia --> Caller
    Caller -->|answers| VAPI_Tofia
    VAPI_Tofia -- "POST /api/patient_conversation" --> FastAPI
    FastAPI -- "after 6 answers" --> Telephony
    Telephony -- "POST /v1/call/phone" --> VAPI_Riley
    VAPI_Riley -->|calls| Hospital
    VAPI_Riley -- "POST /api/hospital_conversation" --> FastAPI
    FastAPI -->|confirmation| Twilio
