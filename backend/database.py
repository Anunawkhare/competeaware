import sqlite3
import json
from datetime import datetime


def init_db():
    conn = sqlite3.connect('competeaware.db')
    c = conn.cursor()

    # Competitors table
    c.execute('''
        CREATE TABLE IF NOT EXISTS competitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            website TEXT,
            social_handles TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Updates table
    c.execute('''
        CREATE TABLE IF NOT EXISTS competitor_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competitor_id INTEGER,
            title TEXT,
            content TEXT,
            category TEXT,
            source TEXT,
            url TEXT,
            impact_score REAL DEFAULT 0.0,
            detected_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (competitor_id) REFERENCES competitors (id)
        )
    ''')

    # Alerts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            update_id INTEGER,
            alert_type TEXT,
            is_read BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()


def get_db_connection():
    conn = sqlite3.connect('competeaware.db')
    conn.row_factory = sqlite3.Row
    return conn