from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import logging
import os
from pymongo import MongoClient

# 🔥 Logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 🔥 CORS (for desktop app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 MongoDB ENV
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise Exception("❌ MONGO_URI not set in environment variables")

# 🔥 MongoDB Connection
client = MongoClient(MONGO_URI)
db = client["coursepilot"]
users_collection = db["users"]


# 🚀 TRACK USER
@app.post("/track")
def track(data: dict):
    try:
        device_id = data.get("device_id")
        course_url = data.get("course_url")
        version = data.get("app_version", "1.0")

        now = datetime.utcnow()

        logging.info(f"Tracking: {device_id} | {course_url}")

        user = users_collection.find_one({"device_id": device_id})

        if user:
            users_collection.update_one(
                {"device_id": device_id},
                {
                    "$set": {
                        "last_seen": now,
                        "app_version": version
                    },
                    "$inc": {"total_sessions": 1}
                }
            )
        else:
            users_collection.insert_one({
                "device_id": device_id,
                "first_seen": now,
                "last_seen": now,
                "total_sessions": 1,
                "app_version": version
            })

        return {"status": "tracked"}

    except Exception as e:
        return {"error": str(e)}


# 📊 TOTAL USERS
@app.get("/total-users")
def total_users():
    count = users_collection.count_documents({})
    return {"total_users": count}


# 📊 ACTIVE USERS (today)
@app.get("/active-users")
def active_users():
    today = datetime.utcnow().date()

    count = users_collection.count_documents({
        "last_seen": {
            "$gte": datetime(today.year, today.month, today.day)
        }
    })

    return {"active_users": count}


# 📊 TOTAL SESSIONS
@app.get("/total-sessions")
def total_sessions():
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$total_sessions"}}}
    ]

    result = list(users_collection.aggregate(pipeline))

    total = result[0]["total"] if result else 0
    return {"total_sessions": total}


# 📊 ALL USERS (DEBUG)
@app.get("/user-stats")
def user_stats():
    users = list(users_collection.find({}, {"_id": 0}))
    return {"users": users}


# ❤️ HEALTH CHECK
@app.get("/health")
def health():
    return {"status": "ok"}
