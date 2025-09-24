import cv2
import requests
import time
import os
import json
from datetime import datetime
import RPi.GPIO as GPIO

# === CONFIG ===
POND_ID = 1  # <<< ตั้งค่าหมายเลขบ่อ
LIMIT_SWITCH_PIN = 18
PWM = 12
INA = 23
INB = 24
LOG_PATH = "/tmp/controller_debug.log"

# 👉 เปลี่ยนเป็น URL ของ cloud app ที่ deploy บน Railway
CLOUD_API_URL = "https://rspi1-production.up.railway.app"  # เปลี่ยนเป็น URL จริง
JOB_CHECK_INTERVAL = 10  # ตรวจสอบงานทุก 10 วินาที

# 👉 ใส่ URL ของ backend main.py (port 8000) สำหรับส่งไฟล์
BACKEND_URL = "https://railwayreal555-production-5be4.up.railway.app/process"

# === LOG FUNCTION ===
def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_PATH, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

# === SETUP GPIO ===
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PWM, GPIO.OUT)
GPIO.setup(INA, GPIO.OUT)
GPIO.setup(INB, GPIO.OUT)
DISTANCE_LIMIT = 30.0  # cm

# === TRY TO INIT I2C SENSOR ===
class DummyChannel:
    @property
    def voltage(self):
        return 1.5  # จำลองค่าแรงดันไฟฟ้า

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    channel = AnalogIn(ads, ADS.P0)
    log("✅ Connected to ADS1115 sensor")
except Exception as e:
    log(f"❌ Can't connect to ADS1115 sensor: {e}")
    channel = DummyChannel()

# === MOTOR CONTROL FUNCTIONS ===
def pull_up():
    GPIO.output(PWM, 10)
    GPIO.output(INA, GPIO.HIGH)
    GPIO.output(INB, GPIO.LOW)

def pull_down():
    GPIO.output(PWM, 10)
    GPIO.output(INA, GPIO.LOW)
    GPIO.output(INB, GPIO.HIGH)

def stop_motor():
    GPIO.output(PWM, 0)
    GPIO.output(INA, GPIO.HIGH)
    GPIO.output(INB, GPIO.LOW)

def wait_for_press():
    close_start = None
    while True:
        try:
            distance = channel.voltage / 3.262 * 100
        except Exception:
            log("⚠️ No sensor data, simulate wait...")
            time.sleep(2)
            break

        if distance <= DISTANCE_LIMIT:
            if close_start is None:
                close_start = time.time()
            elif time.time() - close_start >= 0.2:
                log(f"📏 ระยะ {distance:.2f} cm <= {DISTANCE_LIMIT} cm → เจอวัตถุใกล้ หยุด")
                break
        else:
            close_start = None
        time.sleep(0.1)

def wait_for_release():
    while GPIO.input(LIMIT_SWITCH_PIN) == 0:
        time.sleep(0.01)

# === CLOUD API FUNCTIONS ===
def check_for_job():
    try:
        response = requests.get(f"{CLOUD_API_URL}/job/{POND_ID}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("has_job", False), data.get("job_data")
        else:
            log(f"❌ ตรวจสอบงานล้มเหลว: {response.status_code}")
            return False, None
    except Exception as e:
        log(f"⚠️ ไม่สามารถเชื่อมต่อ cloud: {e}")
        return False, None

def complete_job(result_data):
    try:
        response = requests.post(
            f"{CLOUD_API_URL}/job/{POND_ID}/complete",
            json=result_data,
            timeout=5
        )
        if response.status_code == 200:
            log("✅ แจ้งงานเสร็จเรียบร้อย")
            return True
        else:
            log(f"❌ แจ้งงานเสร็จล้มเหลว: {response.status_code}")
            return False
    except Exception as e:
        log(f"⚠️ ไม่สามารถแจ้งงานเสร็จ: {e}")
        return False

# === MAIN WORK FUNCTION ===
def execute_lift_job(job_data=None):
    log("🔧 เริ่มทำงานยกเชือก...")

    action = "lift"
    if job_data and "action" in job_data:
        action = job_data["action"]

    log(f"📋 Action: {action}")

    try:
        if action == "lift_up":
            log("⬆️ ยกยอขึ้น")
            pull_up()
            wait_for_press()
            stop_motor()
            time.sleep(3)
            log("✅ ยกยอขึ้นเสร็จ")

            # === ถ่ายรูป/วิดีโอ ===
            return capture_and_send(action)

        elif action == "lift_down":
            log("⬇️ ยกยอลง")
            pull_down()
            time.sleep(3)
            stop_motor()
            log("✅ ยกยอลงเสร็จ")

            return {"status": "success", "pond_id": POND_ID, "action": action}

        else:  # default lift
            log("➡️ ดึงมอเตอร์ขึ้น")
            pull_up()
            wait_for_press()
            stop_motor()
            time.sleep(2)

            # ถ่ายรูป/วิดีโอ
            result = capture_and_send(action)

            log("🔄 หมุนมอเตอร์ลง")
            pull_down()
            time.sleep(2)
            stop_motor()
            log("✅ หมุนมอเตอร์ลงเสร็จแล้ว")

            return result

    except Exception as e:
        log(f"🔥 ERROR ในการทำงาน: {e}")
        return {"status": "error", "pond_id": POND_ID, "error": str(e)}

# === CAPTURE FUNCTION ===
def capture_and_send(action):
    log("📷 เปิดกล้อง...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("❌ ไม่สามารถเปิดกล้องได้")

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = 20.0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_filename = f"video_pond{POND_ID}_{timestamp}.mp4"
    image_filename = f"shrimp_pond{POND_ID}_{timestamp}.jpg"

    video_path = os.path.join("/home/rwb/depa", video_filename)
    image_path = os.path.join("/home/rwb/depa", image_filename)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
    start_time = time.time()
    captured_image = None

    while True:
        ret, frame = cap.read()
        if not ret:
            log("❌ ไม่สามารถอ่านภาพจากกล้องได้")
            break

        out.write(frame)

        if captured_image is None and time.time() - start_time > 2.5:
            captured_image = frame.copy()
            cv2.imwrite(image_path, captured_image)
            log(f"📸 ถ่ายภาพนิ่งแล้ว → {image_path}")

        if time.time() - start_time > 5:
            log("⏱️ ครบ 5 วินาที หยุดถ่าย")
            break

    out.release()
    cap.release()

    result_data = {
        "status": "success",
        "pond_id": POND_ID,
        "action": action,
        "timestamp": timestamp,
        "files": {"image": image_filename, "video": video_filename},
    }

    if captured_image is not None:
        log("📤 กำลังส่งไฟล์ไป backend...")
        try:
            with open(image_path, "rb") as img_f, open(video_path, "rb") as vid_f:
                files = [
                    ("files", (image_filename, img_f, "image/jpeg")),
                    ("files", (video_filename, vid_f, "video/mp4")),
                ]
                response = requests.post(BACKEND_URL, files=files)
                if response.status_code == 200:
                    log("✅ ส่งข้อมูลสำเร็จ")
                    result_data["backend_response"] = response.json()
                else:
                    log(f"❌ ส่งข้อมูลล้มเหลว: {response.status_code} - {response.text}")
                    result_data["backend_error"] = f"{response.status_code} - {response.text}"
        except Exception as e:
            log(f"⚠️ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")
            result_data["backend_error"] = str(e)

    return result_data

# === MAIN LOOP ===
def main():
    log("🔌 เริ่มโปรแกรม controller.py (Debug Mode with Camera)")
    log(f"🌐 Cloud API: {CLOUD_API_URL}")
    log(f"🔄 ตรวจสอบงานทุก {JOB_CHECK_INTERVAL} วินาที")

    try:
        while True:
            has_job, job_data = check_for_job()
            if has_job:
                log(f"📋 พบงานใหม่: {job_data}")
                result = execute_lift_job(job_data)
                complete_job(result)
            else:
                log("😴 ไม่มีงาน รอ...")

            time.sleep(JOB_CHECK_INTERVAL)

    except KeyboardInterrupt:
        log("🛑 หยุดโปรแกรมโดยผู้ใช้")
    finally:
        GPIO.cleanup()
        log("🔚 เคลียร์ GPIO แล้ว")

if __name__ == "__main__":
    main()
