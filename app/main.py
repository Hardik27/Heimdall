import os
from fastapi import FastAPI, Request, BackgroundTasks
from app.database import profiles_collection
from app.vectordb import VectorDB
from app.agents import spawn_booking_agents

app = FastAPI()
vector_db = VectorDB(storage_dir=os.getenv("VECTOR_DB_DIR", "./vectors"))

@app.post("/vapi-webhook")
async def vapi_webhook(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    user_id = data.get("phone", "unknown_user")
    transcript = data.get("transcript", "")

    session = vector_db.get_session(user_id)

    # Save the previous answer
    if session.data["index"] > 0:
        session.save_answer(transcript)

    # Ask next question
    question = session.next_question()
    if question:
        return {"type": "text", "content": question}
    else:
        # All questions answered: persist profile & spawn booking agents
        vector_db.add_profile(user_id)
        answers = session.db.sessions[user_id]["answers"]
        profiles_collection.insert_one({"_id": user_id, **answers})
        background_tasks.add_task(spawn_booking_agents, user_id, answers)
        return {
            "type": "text",
            "content": "Thank you! We're searching for the earliest appointment and will notify you when booked."
        }
