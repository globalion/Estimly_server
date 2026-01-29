import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set")

client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database()

users_collection = db.users
companies_collection = db.companies
projects_collection = db.projects
built_in_templates_collection = db.built_in_templates
custom_templates_collection = db.custom_templates
