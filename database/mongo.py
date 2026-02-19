import os
from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = os.getenv("MONGO_URL")

if not MONGO_URL:
    raise RuntimeError("MONGO_URL is not set")

client = AsyncIOMotorClient(MONGO_URL)
db = client.get_database()

users_collection = db["users"]
projects_collection = db["projects"]
companies_collection = db["companies"]
invites_collection = db["invites_collection"]
resource_roles_collection = db["resource_roles"]
custom_templates_collection = db["custom_templates"]
built_in_templates_collection = db["built_in_templates"]
estimation_settings_collection = db["estimation_settings"]
estimation_techniques_collection = db["estimation_techniques"]
resource_rate_history_collection = db["resource_rate_history"]
subscriptions_collection = db["subscriptions"]
payments_collection = db["payments"]
