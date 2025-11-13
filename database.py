import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            timestamp TEXT NOT NULL,
            accel_x REAL NOT NULL,
            accel_y REAL NOT NULL,
            accel_z REAL NOT NULL,
            temperature REAL NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


def insert_data(timestamp, ax, ay, az, temp):
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO sensor_data (timestamp, accel_x, accel_y, accel_z, temperature)
            VALUES (%s, %s, %s, %s, %s);
        """, (timestamp, ax, ay, az, temp))

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        print("🔥 POSTGRES INSERT ERROR:", e)
