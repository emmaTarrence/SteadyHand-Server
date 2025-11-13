import sqlite3
import os

# Use Render-approved writable directory
PERSIST_DIR = "/opt/render/project/.data"
DB_PATH = f"{PERSIST_DIR}/steadyhand.db"

def init_db():
    # Make sure the directory exists
    os.makedirs(PERSIST_DIR, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

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

    # Use WAL mode for concurrency safety
    c.execute("PRAGMA journal_mode=WAL;")

    conn.commit()
    conn.close()


def insert_data(timestamp, ax, ay, az, temp):
    try:
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
