import requests

SERVER_URL = "https://steadyhand-server.onrender.com/data"

def fetch_data(limit=1000):
    try:
        response = requests.get(SERVER_URL, params={"limit": limit})
        response.raise_for_status()  # throw error if not 200

        data = response.json()
        return data["data"]  # server returns {"data": [...]}

    except Exception as e:
        print("Error fetching data:", e)
        return []

if __name__ == "__main__":
    rows = fetch_data(limit=300)  # change limit as needed

    print("Fetched", len(rows), "rows:\n")

    for row in rows:  # print first 10
        print(row)
