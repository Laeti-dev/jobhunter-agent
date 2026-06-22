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
