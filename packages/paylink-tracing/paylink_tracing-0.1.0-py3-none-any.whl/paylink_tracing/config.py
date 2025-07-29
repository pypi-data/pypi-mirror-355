import os
from dotenv import load_dotenv


load_dotenv(override=True)

MONGO_URI = os.getenv("MONGO_URI")
ENV = os.getenv("ENV", "development")


