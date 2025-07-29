from pymongo import MongoClient
from pymongo.server_api import ServerApi
from paylink_tracing.config import MONGO_URI


client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
db = client["paylink_tracing"]
trace_collection = db["traces"]
