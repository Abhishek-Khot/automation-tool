from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import sqlite3
import logging

# 🔥 Setup logging
logging.basicConfig(level=logging.INFO)

app = FastAPI()

# 🔥 Enable CORS (important for desktop app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔥 Database setup
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT UNIQUE,
    first_seen TEXT,
    last_seen TEXT,
    total_sessions INTEGER,
    app_version TEXT
)
""")
conn.commit()


# 🚀 TRACK USER
@app.post("/track")
def track(data: dict):
    try:
        device_id = data.get("device_id")
        course_url = data.get("course_url")
        version = data.get("app_version", "1.0")

        now = datetime.now().isoformat()

        logging.info(f"Tracking: {device_id} | {course_url}")

        cursor.execute("SELECT * FROM users WHERE device_id=?", (device_id,))
        user = cursor.fetchone()

        if user:
            cursor.execute("""
                UPDATE users 
                SET last_seen=?, total_sessions=total_sessions+1, app_version=?
                WHERE device_id=?
            """, (now, version, device_id))
        else:
            cursor.execute("""
                INSERT INTO users (device_id, first_seen, last_seen, total_sessions, app_version)
                VALUES (?, ?, ?, ?, ?)
            """, (device_id, now, now, 1, version))

        conn.commit()

        return {"status": "tracked"}

    except Exception as e:
        return {"error": str(e)}


# 📊 TOTAL USERS
@app.get("/total-users")
def total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return {"total_users": cursor.fetchone()[0]}


# 📊 ACTIVE USERS (today)
@app.get("/active-users")
def active_users():
    today = datetime.now().date().isoformat()

    cursor.execute("""
        SELECT COUNT(*) FROM users 
        WHERE DATE(last_seen)=?
    """, (today,))

    return {"active_users": cursor.fetchone()[0]}


# 📊 TOTAL SESSIONS
@app.get("/total-sessions")
def total_sessions():
    cursor.execute("SELECT SUM(total_sessions) FROM users")
    result = cursor.fetchone()[0]
    return {"total_sessions": result if result else 0}


# 📊 ALL USERS (DEBUG)
@app.get("/user-stats")
def user_stats():
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()

    return {
        "users": [
            {
                "device_id": r[1],
                "first_seen": r[2],
                "last_seen": r[3],
                "total_sessions": r[4],
                "version": r[5],
            }
            for r in rows
        ]
    }


# ❤️ HEALTH CHECK
@app.get("/health")
def health():
    return {"status": "ok"}
