import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# -------------------------------------------------------------------
# INITIALIZE BOTH TABLES
# -------------------------------------------------------------------
def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Raw high-frequency IMU data
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

    # Archive table storing 1-minute summaries
    cur.execute("""
        CREATE TABLE IF NOT EXISTS archive_data (
            id SERIAL PRIMARY KEY,
            minute_start TIMESTAMP NOT NULL,
            avg_accel REAL NOT NULL,
            avg_temp REAL NOT NULL
        );
    """)

    conn.commit()
    cur.close()
    conn.close()


# -------------------------------------------------------------------
# INSERT RAW DATA
# -------------------------------------------------------------------
def insert_data(timestamp, ax, ay, az, temp, conn):
    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO sensor_data (timestamp, accel_x, accel_y, accel_z, temperature)
            VALUES (%s, %s, %s, %s, %s);
        """, (timestamp, ax, ay, az, temp))

        conn.commit()
        cur.close()

    except Exception as e:
        print("🔥 POSTGRES INSERT ERROR:", e)


# -------------------------------------------------------------------
# ARCHIVE DATA OLDER THAN 1 WEEK
# -------------------------------------------------------------------
def archive_old_data(conn):
    try:
        cur = conn.cursor()

        # 1. Convert timestamp text → real timestamp
        # 2. Filter older than 7 days
        # 3. Group by minute
        # 4. Compute averages
        cur.execute("""
            INSERT INTO archive_data (minute_start, avg_accel, avg_temp)
            SELECT
                date_trunc('minute', timestamp::timestamp) AS minute_start,
                AVG(SQRT(accel_x*accel_x + accel_y*accel_y + accel_z*accel_z)) AS avg_accel,
                AVG(temperature) AS avg_temp
            FROM sensor_data
            WHERE timestamp::timestamp < NOW() - INTERVAL '7 days'
            GROUP BY minute_start
            ORDER BY minute_start;
        """)

        # 5. Delete high-frequency rows older than 1 week
        cur.execute("""
            DELETE FROM sensor_data
            WHERE timestamp::timestamp < NOW() - INTERVAL '7 days';
        """)

        conn.commit()
        cur.close()

    except Exception as e:
        print("🔥 ARCHIVE ERROR:", e)
        
def backup_sensor_data():
    """Save current data so we can restore it later."""
    conn = get_connection()
    cur = conn.cursor()
    # optional: drop old backup if it exists
    cur.execute("DROP TABLE IF EXISTS sensor_data_backup;")
    cur.execute("CREATE TABLE sensor_data_backup AS TABLE sensor_data;")
    conn.commit()
    cur.close()
    conn.close()
    print("Backed up current sensor_data into sensor_data_backup.")

def restore_sensor_data():
    """Restore data from the backup table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE TABLE sensor_data;")
    cur.execute("INSERT INTO sensor_data SELECT * FROM sensor_data_backup;")
    conn.commit()
    cur.close()
    conn.close()
    print("Restored sensor_data from sensor_data_backup.")

def seed_fake_week(num_samples=5_670_000):
    """
    Insert synthetic 1 week of data at 50 Hz (≈5.67M samples).
    Uses a single bulk INSERT with generate_series for speed.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sensor_data (timestamp, accel_x, accel_y, accel_z, temperature)
        SELECT
            -- simulate timestamps at 50 Hz (every 20 ms)
            to_char(
                NOW() + (n * interval '20 milliseconds'),
                'YYYY-MM-DD"T"HH24:MI:SS.MS'
            ) AS timestamp,
            (random()*2 - 1)::real AS accel_x,
            (random()*2 - 1)::real AS accel_y,
            (random()*2 - 1)::real AS accel_z,
            (25 + random()*5)::real AS temperature
        FROM generate_series(1, %s) AS s(n);
    """, (num_samples,))
    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {num_samples} fake samples.")