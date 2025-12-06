from fastapi import FastAPI
from pydantic import BaseModel
from database import init_db, insert_data, get_connection
from datetime import datetime, timedelta
from typing import List, Union
import os

ACC_SCALE = 1.0 / 16384.0  # adjust to match your IMU

print("📌 DATABASE_URL = ", os.environ.get("DATABASE_URL"))

app = FastAPI()
init_db()

class SensorPacket(BaseModel):
    timestamp: str
    samples: list[int]

@app.get("/")
def home():
    return {"message": "sup biotch"}

@app.get("/debug-db")
def debug_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM sensor_data;")
        count = cur.fetchone()
        cur.close()
        conn.close()
        return {"rows_in_postgres": count}
    except Exception as e:
        return {"error": str(e)}

# @app.post("/upload")
# async def upload_data(packets: Union[dict, List[dict]]):
#     # Convert single packet to list
#     if isinstance(packets, dict):
#         packets = [packets]

#     saved_count = 0

#     for packet in packets:
#         ts = packet.get("timestamp")

#         if isinstance(ts, (list, tuple)) and len(ts) >= 6:
#             try:
#                 year, mon, day, hour, minute, second = ts[:6]
#                 timestamp = datetime(year, mon, day, hour, minute, second).isoformat()
#             except Exception:
#                 timestamp = datetime.utcnow().isoformat()
#         elif isinstance(ts, str):
#             timestamp = ts
#         else:
#             timestamp = datetime.utcnow().isoformat()

#         accel_x = packet.get("accel_x", 0.0)
#         accel_y = packet.get("accel_y", 0.0)
#         accel_z = packet.get("accel_z", 0.0)
#         temperature = packet.get("temperature", 0.0)

#         insert_data(timestamp, accel_x, accel_y, accel_z, temperature)
#         saved_count += 1

#     print(f"✅ Saved {saved_count} entries")
#     return {"status": "success", "records_saved": saved_count}

@app.post("/upload")
async def upload_data(packets: Union[dict, List[dict]]):
    # Normalize to list
    if isinstance(packets, dict):
        packets = [packets]

    saved_count = 0

    for packet in packets:
        if "samples" not in packet:
            continue

        ts = packet.get("timestamp")

        # Base timestamp: Unix seconds -> datetime
        if isinstance(ts, (int, float)):
            base_dt = datetime.utcfromtimestamp(ts)
        else:
            base_dt = datetime.utcnow()

        # Sample period: default 20 ms (50 Hz), but allow override
        period_ms = packet.get("period_ms", 20)
        period_sec = period_ms / 1000.0

        samples = packet.get("samples") or []

        # Normalize samples:
        # - if samples[0] is list/tuple, assume [[ax,ay,az,temp], ...]
        # - else assume flat [ax0,ay0,az0,temp0,ax1,...] and chunk into 4s
        if samples and isinstance(samples[0], (list, tuple)):
            normalized_samples = samples
        else:
            normalized_samples = []
            CHUNK = 4  # ax, ay, az, temp
            for i in range(0, len(samples), CHUNK):
                chunk = samples[i:i + CHUNK]
                if len(chunk) == CHUNK:
                    normalized_samples.append(chunk)

        # Now insert each sample with its own offset timestamp
        for idx, sample in enumerate(normalized_samples):
            raw_ax, raw_ay, raw_az, raw_temp = sample

            # timestamp for this specific sample
            sample_dt = base_dt + timedelta(seconds=idx * period_sec)
            timestamp_str = sample_dt.isoformat()

            accel_x = float(raw_ax) * ACC_SCALE
            accel_y = float(raw_ay) * ACC_SCALE
            accel_z = float(raw_az) * ACC_SCALE
            temperature = float(raw_temp)

            insert_data(timestamp_str, accel_x, accel_y, accel_z, temperature)
            saved_count += 1

    # archive_old_data()
    return {"status": "success", "records_saved": saved_count}

@app.get("/data")
async def get_data(limit: int = 1000):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, timestamp, accel_x, accel_y, accel_z, temperature
        FROM sensor_data
        ORDER BY id DESC
        LIMIT %s;
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    # Convert snake_case → PascalCase for MAUI
    normalized = [
        {
            "Id": row["id"],
            "Timestamp": row["timestamp"],
            "AccelX": row["accel_x"],
            "AccelY": row["accel_y"],
            "AccelZ": row["accel_z"],
            "Temperature": row["temperature"],
        }
        for row in rows
    ]

    return {"data": normalized}
