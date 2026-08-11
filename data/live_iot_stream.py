import sqlite3
import random
import uuid
import time
from datetime import datetime

# ⚠️ Ensure this matches the exact DB path you found earlier!
DB_NAME = "data/facilityops.db" 

def stream_live_data():
    print("🚀 Starting Live IoT Telemetry Stream...")
    print("Agentic FacilityOPS is now listening to simulated edge sensors.")
    print("Press Ctrl+C to stop the stream.\n")

    while True:
        try:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            now = datetime.now()
            
            # Generate realistic current usage (fluctuating baseline)
            base_kwh = random.uniform(150, 200)
            
            # 5% chance of a random massive spike to simulate an anomaly for the demo
            if random.random() > 0.95:
                base_kwh += random.uniform(100, 300)
                print(f"⚠️ [ANOMALY DETECTED] HVAC load spiked at {now.strftime('%H:%M:%S')}!")

            peak_kw = base_kwh * random.uniform(1.1, 1.3)
            cost = base_kwh * 0.12
            record_id = str(uuid.uuid4())
            timestamp_iso = now.isoformat()

            # Insert the live reading into the database
            cursor.execute("""
                INSERT INTO energy_usage (record_id, facility_id, timestamp, energy_kwh, peak_demand_kw, cost)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (record_id, "FAC-001", timestamp_iso, round(base_kwh, 2), round(peak_kw, 2), round(cost, 2)))

            conn.commit()
            conn.close()

            print(f"[{now.strftime('%H:%M:%S')}] Streamed 1 IoT record -> {round(base_kwh, 2)} kWh")
            
            # Wait 5 seconds before the next sensor reading
            time.sleep(5) 

        except Exception as e:
            print(f"❌ Database connection error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    stream_live_data()