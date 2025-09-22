import cv2
import requests
import time
import os
from datetime import datetime
import RPi.GPIO as GPIO

# === CONFIG ===
POND_ID = 1  # <<< ตั้งค่าหมายเลขบ่อ
LIMIT_SWITCH_PIN = 18
PWM = 12
INA = 23
INB = 24
LOG_PATH = "/tmp/controller_debug.log"

# 👉 ใส่ ngrok URL ของ backend main.py (port 8000)
SERVER_URL = "https://7dd73855e55a.ngrok-free.app/process"

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
DISTANCE_LIMIT = 30.0  # cm (ตั้งตามที่ต้องการ)

import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
channel = AnalogIn(ads, ADS.P0)

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
        distance = channel.voltage / 3.262 * 100
        if distance <= DISTANCE_LIMIT:
            if close_start is None:
                close_start = time.time()
            elif time.time() - close_start >= 0.2:
                log(f"📏 ระยะ {distance:.2f} cm <= {DISTANCE_LIMIT} cm → เจอวัตถุใกล้นานเกิน 1 วินาที หยุด")
                break
        else:
            close_start = None
        time.sleep(0.1)

def wait_for_release():
    while GPIO.input(LIMIT_SWITCH_PIN) == 0:
        time.sleep(0.01)

# === START LOGIC ===
try:
    log("🔌 เริ่มโปรแกรม controller.py")

    log("➡️ ดึงมอเตอร์ขึ้น")
    start_up_time = time.time()
    pull_up()
    log("🕹️ รอปุ่มกด (limit switch)")
    wait_for_press()
    stop_motor()
    time.sleep(3)
    duration_up = time.time() - start_up_time
    pull_down()
    time.sleep(duration_up)
    stop_motor()
    log(f"✅ กดปุ่มแล้ว หยุดดึงขึ้น (ใช้เวลา {duration_up:.2f} วินาที)")

    log("📷 เตรียมกล้อง...")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        log("❌ ไม่สามารถเปิดกล้องได้")
        raise RuntimeError("เปิดกล้องไม่ได้")

    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = 20.0

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ✅ เพิ่ม pond_id ในชื่อไฟล์
    video_filename = f"video_pond{POND_ID}_{timestamp}.mp4"
    image_filename = f"shrimp_pond{POND_ID}_{timestamp}.jpg"

    video_path = os.path.join("/home/rwb/depa", video_filename)
    image_path = os.path.join("/home/rwb/depa", image_filename)
    os.makedirs(os.path.dirname(video_path), exist_ok=True)

    log("🎥 เริ่มถ่ายวิดีโอ")
    out = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
    start_time = time.time()
    captured_image = None
    stop_motor()

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

    if captured_image is not None:
        log("📤 กำลังส่งภาพและวิดีโอไปยังเซิร์ฟเวอร์...")
        try:
            with open(image_path, "rb") as img_f, open(video_path, "rb") as vid_f:
                files = [
                    ("files", (image_filename, img_f, "image/jpeg")),
                    ("files", (video_filename, vid_f, "video/mp4"))
                ]
                response = requests.post(SERVER_URL, files=files)
                if response.status_code == 200:
                    log("✅ ส่งข้อมูลสำเร็จ")
                    log(response.json())
                else:
                    log(f"❌ ส่งข้อมูลล้มเหลว: {response.status_code} - {response.text}")
        except Exception as e:
            log(f"⚠️ เกิดข้อผิดพลาดในการส่งข้อมูล: {e}")
    else:
        log("⚠️ ไม่มีภาพนิ่งจะส่ง")

    log("🔄 หมุนมอเตอร์ลง")
    pull_down()
    time.sleep(duration_up)
    stop_motor()
    log("✅ หมุนมอเตอร์ลงเสร็จแล้ว")

except KeyboardInterrupt:
    log("🛑 หยุดโปรแกรมโดยผู้ใช้")
except Exception as e:
    log(f"🔥 ERROR: {e}")
finally:
    cap.release()
    GPIO.cleanup()
    log("🔚 ปิดกล้องและเคลียร์ GPIO แล้ว")
