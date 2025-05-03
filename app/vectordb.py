import os
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings

class Session:
    def __init__(self, db, user_id):
        self.db = db
        self.user_id = user_id
        self.data = db.sessions[user_id]

    def next_question(self):
        idx = self.data["index"]
        if idx < len(self.db.questions):
            q = self.db.questions[idx]
            self.data["index"] += 1
            return q
        return None

    def save_answer(self, answer):
        key = self.db.questions[self.data["index"] - 1]
        self.data["answers"][key] = answer

class VectorDB:
    def __init__(self, storage_dir):
        self.questions = [
            "What’s your full name?",
            "What’s your date of birth?",
            "What’s your phone number or email?",
            "Do you have health insurance?",
            "Which insurance provider do you use?",
            "Are there any hospitals or clinics you prefer?",
            "What city or ZIP code are you in?",
            "What is this appointment for?",
            "Is this urgent?",
            "Do you prefer a male or female doctor?",
            "Do you prefer morning or afternoon appointments?"
        ]
        self.sessions = {}
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = chromadb.PersistentClient(path=storage_dir, settings=Settings())
        self.collection = self.client.get_or_create_collection("patients")

    def start_session(self, user_id):
        self.sessions[user_id] = {"answers": {}, "index": 0}

    def get_session(self, user_id):
        if user_id not in self.sessions:
            self.start_session(user_id)
        return Session(self, user_id)

    def add_profile(self, user_id):
        answers = self.sessions[user_id]["answers"]
        text = " ".join([f"{k}: {v}" for k, v in answers.items()])
        embedding = self.model.encode(text).tolist()
        self.collection.add(
            ids=[user_id],
            embeddings=[embedding],
            metadatas=[answers],
            documents=[text]
        )
