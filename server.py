from fastapi import FastAPI
from pydantic import BaseModel
from database import init_db, insert_data
import sqlite3
from datetime import datetime

app = FastAPI()
init_db()

class SensorPacket(BaseModel):
    timestamp: str
    accel_x: float
    accel_y: float
    accel_z: float
    temperature: float
    

@app.get("/")
def home():
    return {"message": "sup biotch"}

@app.post("/upload")
async def upload_data(packets: Union[dict, List[dict]]):
    """
    Accepts a single sensor packet OR a list of packets.
    """
    # Convert single packet to list for consistent handling
    if isinstance(packets, dict):
        packets = [packets]

    saved_count = 0

    for packet in packets:
        ts = packet.get("timestamp")

        # Handle ESP32-style timestamps (like [year, month, day, hour, min, sec])
        if isinstance(ts, (list, tuple)) and len(ts) >= 6:
            try:
                year, mon, day, hour, minute, second = ts[:6]
                timestamp = datetime(year, mon, day, hour, minute, second).isoformat()
            except Exception:
                timestamp = datetime.utcnow().isoformat()
        elif isinstance(ts, str):
            timestamp = ts
        else:
            timestamp = datetime.utcnow().isoformat()

        accel_x = packet.get("accel_x", 0.0)
        accel_y = packet.get("accel_y", 0.0)
        accel_z = packet.get("accel_z", 0.0)
        temperature = packet.get("temperature", 0.0)

        insert_data(timestamp, accel_x, accel_y, accel_z, temperature)
        saved_count += 1

    print(f"✅ Saved {saved_count} entries")
    return {"status": "success", "records_saved": saved_count}

@app.get("/data")
async def get_data(limit: int = 1000):
    conn = sqlite3.connect("data/steadyhand.db")
    c = conn.cursor()
    c.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()

    print("[SERVER] Most recent timestamps:")
    for r in rows[:5]:
        print(" →", r[1])

    return {"data": rows}
