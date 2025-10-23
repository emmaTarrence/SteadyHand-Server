from fastapi import FastAPI
from pydantic import BaseModel
from database import init_db, insert_data
import sqlite3

app = FastAPI()
init_db()

class SensorPacket(BaseModel):
    timestamp: str
    accel_x: float
    accel_y: float
    accel_z: float
    temperature: float

@app.post("/upload")
async def upload_data(packet: SensorPacket):
    insert_data(packet.timestamp, packet.accel_x, packet.accel_y, packet.accel_z, packet.temperature)
    return {"status": "success"}

@app.get("/data")
async def get_data(limit: int = 1000):
    conn = sqlite3.connect("data/steadyhand.db")
    c = conn.cursor()
    c.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return {"data": rows}
