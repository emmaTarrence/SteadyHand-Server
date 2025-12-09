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
        archive_old_data(conn)

    except Exception as e:
        print("🔥 POSTGRES INSERT ERROR:", e)


# -------------------------------------------------------------------
# ARCHIVE DATA OLDER THAN 1 WEEK
MAX_ROWS = 5_670_000  # 7 days @ 4.5 hours/day, 50 Hz

def archive_old_data(conn, max_rows: int = MAX_ROWS):
    try:
        cur = conn.cursor()

        # 1. How many rows do we have?
        cur.execute("SELECT COUNT(*) AS count FROM sensor_data;")
        total = cur.fetchone()["count"]

        if total <= max_rows:
            # Nothing to archive yet
            print(f"No archiving needed. total={total}, limit={max_rows}")
            cur.close()
            return

        rows_to_trim = total - max_rows
        print(f"Archiving oldest {rows_to_trim} rows (total={total}, limit={max_rows})")

        # 2. Find a cutoff timestamp such that everything up to that point
        #    represents approximately `rows_to_trim` oldest rows.
        #    We take the timestamp of the `rows_to_trim`-th oldest sample.
        cur.execute("""
            SELECT timestamp::timestamp AS cutoff_ts
            FROM sensor_data
            ORDER BY timestamp::timestamp
            OFFSET %s - 1
            LIMIT 1;
        """, (rows_to_trim,))

        row = cur.fetchone()
        if not row or row["cutoff_ts"] is None:
            print("⚠️ Could not determine cutoff timestamp; aborting archive.")
            cur.close()
            return

        cutoff_ts = row["cutoff_ts"]
        print(f"Using cutoff_ts={cutoff_ts} for archiving.")

        # 3. Archive all rows up to that cutoff, summarized by minute
        cur.execute("""
            INSERT INTO archive_data (minute_start, avg_accel, avg_temp)
            SELECT
                date_trunc('minute', timestamp::timestamp) AS minute_start,
                AVG(SQRT(accel_x*accel_x + accel_y*accel_y + accel_z*accel_z)) AS avg_accel,
                AVG(temperature) AS avg_temp
            FROM sensor_data
            WHERE timestamp::timestamp <= %s
            GROUP BY minute_start
            ORDER BY minute_start;
        """, (cutoff_ts,))

        # 4. Delete the high-frequency rows we just summarized
        cur.execute("""
            DELETE FROM sensor_data
            WHERE timestamp::timestamp <= %s;
        """, (cutoff_ts,))

        conn.commit()
        cur.close()
        print("✅ Archive + delete complete.")

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

def seed_fake_week(target_rows=5_670_000):
    """
    Ensure the sensor_data table has ~target_rows samples.
    It checks how many rows exist and only inserts the difference.
    """
    conn = get_connection()
    cur = conn.cursor()

    # How many rows are there now?
    cur.execute("SELECT COUNT(*) AS count FROM sensor_data;")
    row = cur.fetchone()
    current = row["count"]          # <-- dict key, not index
    remaining = target_rows - current

    print(f"Current rows: {current}, need to add: {remaining}")

    if remaining <= 0:
        print("Already at or above target; nothing to insert.")
        cur.close()
        conn.close()
        return

    # Insert only the remaining rows
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
    """, (remaining,))

    conn.commit()
    cur.close()
    conn.close()
    print(f"Inserted {remaining} fake samples (now close to {target_rows}).")
