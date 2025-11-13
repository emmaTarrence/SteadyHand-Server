import sqlite3
import os

# Render persistent storage location
DB_PATH = "/var/data/steadyhand.db"


def init_db():
    # Ensure persistent directory exists
    os.makedirs("/var/data", exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            temperature REAL
        );
    """)

    # Prevent SQLite locking issues
    c.execute("PRAGMA journal_mode=WAL;")

    conn.commit()
    conn.close()


def insert_data(timestamp, ax, ay, az, temp):
    try:
        # timeout helps avoid locking crashes
        conn = sqlite3.connect(DB_PATH, timeout=5)
        c = conn.cursor()

        c.execute("""
            INSERT INTO sensor_data
            (timestamp, accel_x, accel_y, accel_z, temperature)
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, ax, ay, az, temp))

        conn.commit()
        conn.close()

    except Exception as e:
        print("🔥 SQLITE INSERT ERROR:", e)
