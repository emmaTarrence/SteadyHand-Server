import sqlite3

def init_db():
    conn = sqlite3.connect("data/steadyhand.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            accel_x REAL,
            accel_y REAL,
            accel_z REAL,
            temperature REAL
        )
    """)
    conn.commit()
    conn.close()

def insert_data(timestamp, ax, ay, az, temp):
    conn = sqlite3.connect("data/steadyhand.db")
    c = conn.cursor()
    c.execute(
        "INSERT INTO sensor_data (timestamp, accel_x, accel_y, accel_z, temperature) VALUES (?, ?, ?, ?, ?)",
        (timestamp, ax, ay, az, temp)
    )
    conn.commit()
    conn.close()
