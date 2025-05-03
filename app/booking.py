from datetime import datetime, timedelta

def try_book_appointment(answers):
    # Simulate finding the next-day slot
    scheduled_time = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
    location = answers.get("Are there any hospitals or clinics you prefer?", "Nearest clinic")
    return True, {"time": scheduled_time, "location": location}
