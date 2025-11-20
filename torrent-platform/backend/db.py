from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://hoxha:Niguarda20162@cluster0.ktcp4fk.mongodb.net/")
DB_NAME = os.getenv("DB_NAME", "torrent_platform")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

users_col = db["users"]
torrents_col = db["torrents"]
comments_col = db["comments"]
downloads_col = db["downloads"]
