import requests
import time
import os
from datetime import datetime

# === CONFIG ===
POND_ID = 1  # <<< ตั้งค่าหมายเลขบ่อ
LOG_PATH = "/tmp/heartbeat_debug.log"

# === LOG FUNCTION ===
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

# === HEARTBEAT FUNCTION ===
def send_heartbeat():
    """ส่งสัญญาณ heartbeat ไปยังเซิร์ฟเวอร์"""
    try:
        heartbeat_data = {
            "device_id": f"raspi_pond_{POND_ID}",
            "status": "online",
            "timestamp": datetime.now().isoformat(),
            "pond_id": POND_ID
        }
        
        url = "https://railwayreal555-production-5be4.up.railway.app/heartbeat"
        log(f"🌐 Sending heartbeat to: {url}")
        log(f"📤 Data: {heartbeat_data}")
        
        response = requests.post(
            url,
            json=heartbeat_data,
            timeout=10
        )
        
        log(f"📥 Response status: {response.status_code}")
        log(f"📥 Response text: {response.text}")
        
        if response.status_code == 200:
            log("💓 Heartbeat ส่งสำเร็จ")
            return True
        else:
            log(f"❌ Heartbeat ล้มเหลว: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        log(f"⚠️ Heartbeat Error: {e}")
        log(f"⚠️ Error type: {type(e).__name__}")
        return False

# === MAIN HEARTBEAT LOOP ===
def main():
    log("💓 เริ่มโปรแกรม heartbeat.py")
    log(f"🔄 ส่ง Heartbeat ทุก 5 วินาที")
    
    try:
        while True:
            send_heartbeat()
            time.sleep(5)  # ส่งทุก 5 วินาที
            
    except KeyboardInterrupt:
        log("🛑 หยุดโปรแกรม heartbeat โดยผู้ใช้")
    except Exception as e:
        log(f"🔥 ERROR: {e}")

if __name__ == "__main__":
    main()
