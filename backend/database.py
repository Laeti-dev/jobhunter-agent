import sqlite3
import json
from cv_model import CVProfile

DB_PATH = "cv_database.db"

def init_db():
    """Create the cv_profile table if does not exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cv_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT
            )
        """)
        conn.commit()

def get_connection():
    return sqlite3.connect(DB_PATH)

def save_cv(profile: CVProfile) -> int:
    """Save the CV profile to the database and returns its ID."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO cv_profile (name, data) VALUES (?, ?)
        """, (profile.name, profile.model_dump_json()))
        return cursor.lastrowid

def get_latest_cv() -> CVProfile | None:
    """Retrieve the most recent CV profile from the database."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT * FROM cv_profile ORDER BY created_at DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return CVProfile.model_validate_json(row[3])
        return None
