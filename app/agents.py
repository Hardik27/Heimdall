import os
from celery import Celery, group
from app.booking import try_book_appointment
from app.database import appointments_collection

celery_app = Celery(
    "agents",
    broker=os.getenv("CELERY_BROKER_URL"),
    backend=os.getenv("CELERY_RESULT_BACKEND")
)

@celery_app.task
def agent_task(user_id, answers, agent_id):
    import random, time
    time.sleep(random.uniform(1,3))
    success, details = try_book_appointment(answers)
    return {"agent": agent_id, "success": success, "details": details}

def spawn_booking_agents(user_id, answers):
    tasks = [
        agent_task.s(user_id, answers, f"agent_{i+1}")
        for i in range(3)
    ]
    job = group(tasks)()
    # Save Celery job ID so you can fetch results later
    appointments_collection.update_one(
        {"_id": user_id},
        {"$set": {"booking_job_id": job.id}}
    )
