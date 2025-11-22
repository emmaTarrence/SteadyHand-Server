# SteadyHand Server

Backend API for the SteadyHand Senior Design Project  
FastAPI + PostgreSQL, deployed on Render

---

## Overview

The SteadyHand Server provides the backend infrastructure for the SteadyHand sensor system.  
It receives high-frequency IMU data from an ESP32-based device, normalizes the samples, stores them in PostgreSQL, and exposes REST endpoints for the MAUI app.

---

## Technology Stack

Component | Technology  
--------- | ----------  
Backend Framework | FastAPI  
Language | Python 3  
Database | PostgreSQL (Render-hosted)  
Deployment | Render Web Service  
DB Access | psycopg2  
Input Model | pydantic  

---

## Repository Structure

SteadyHand-Server/  
│  
├── server.py         (Main FastAPI app, routes, logic)  
├── database.py       (DB connection, schema creation, insert helpers)  
├── requirements.txt  (Python dependencies)  
├── data/             (optional local data files)  
└── ...  

---

# API Documentation

Real routes implemented in server.py:

---

## GET /

Health check route.

Response:  
{ "message": "Hello World" }

---

## GET /debug-db

Returns number of rows in sensor_data table.

Response:  
{ "rows_in_postgres": [1234] }

---

## POST /upload

Uploads IMU samples from ESP32.

Supports:

- single packet or list  
- unix timestamps  
- flat or nested arrays  
- timestamp reconstruction  
- scaling to g’s  

Packet Format (Flat):  
{ "timestamp": 1732300000, "period_ms": 20, "samples": [ax0, ay0, az0, temp0, ax1, ay1, az1, temp1] }

Packet Format (Chunked):  
{ "timestamp": 1732300000, "samples": [[ax0, ay0, az0, temp0], [ax1, ay1, az1, temp1]] }

Processing logic:  
1. Interpret timestamp  
2. Expand flat samples  
3. Compute per-sample timestamps  
4. Scale accel values using raw/16384  

Success Response:  
{ "status": "success", "records_saved": 150 }

---

## GET /data

Returns most recent sensor samples.

Query Params:  
limit = number of rows (default 1000)

Response format (PascalCase):  
Id, Timestamp, AccelX, AccelY, AccelZ, Temperature

---

# Database Schema

CREATE TABLE IF NOT EXISTS sensor_data (  
  id SERIAL PRIMARY KEY,  
  timestamp TEXT NOT NULL,  
  accel_x REAL NOT NULL,  
  accel_y REAL NOT NULL,  
  accel_z REAL NOT NULL,  
  temperature REAL NOT NULL  
);

---

# Running Locally

1. Clone repo  
git clone https://github.com/emmaTarrence/SteadyHand-Server  
cd SteadyHand-Server

2. Create venv  
python3 -m venv venv  
source venv/bin/activate

3. Install deps  
pip install -r requirements.txt

4. Run server  
uvicorn server:app --reload

5. Required env var:  
DATABASE_URL=<Render_Postgres_URL>

---

# Deployment on Render

Build command:  
pip install -r requirements.txt

Start command:  
uvicorn server:app --host 0.0.0.0 --port $PORT

Deployment URL:  
https://steadyhand-server.onrender.com

---

# Testing

Upload packet:  
curl -X POST https://steadyhand-server.onrender.com/upload -H "Content-Type: application/json" -d "{\"timestamp\":1732300000,\"samples\":[1000,2000,3000,25]}"

Fetch rows:  
curl https://steadyhand-server.onrender.com/data?limit=5

Check DB:  
curl https://steadyhand-server.onrender.com/debug-db

---



## Team Contacts

| Name          | Role                            | Email                                             |
| ------------- | ------------------------------- | ------------------------------------------------- |
| Anna Babus    | Team Lead / Power & Bluetooth   | [ababus@purdue.edu](mailto:ababus@purdue.edu)     |
| Jason Reust   | Motor & Sensor Implementation   | [reustj@purdue.edu](mailto:reustj@purdue.edu)     |
| Noah Bonahoom | Embedded Software / Facilitator | [nbonahoo@purdue.edu](mailto:nbonahoo@purdue.edu) |
| Emma Tarrence | App & Database / Communicator   | [etarrenc@purdue.edu](mailto:etarrenc@purdue.edu) |
| Jordan Weiler | WiFi Integration / Budgeter     | [weiler7@purdue.edu](mailto:weiler7@purdue.edu)   |
