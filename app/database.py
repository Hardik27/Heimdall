import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

profiles_collection = db["profiles"]
appointments_collection = db["appointments"]
