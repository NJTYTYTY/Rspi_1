#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import requests
import cv2
import RPi.GPIO as GPIO
import os
from datetime import datetime
from camera import open_camera
from motor import pull_up, pull_down, stop_motor, wait_for_press

# === CONFIG ===
POND_ID = 1
BACKEND_URL = "http://192.168.1.60:3000/api/pond-status/{POND_ID}"
JOB_CHECK_INTERVAL = 5  # วินาที
FRONT_API_URL = "https://main-two-peach.vercel.app"

# 👉 เปลี่ยนเป็น URL ของ cloud app ที่ deploy บน Railway
CLOUD_API_URL = "https://rspi1-production.up.railway.app"  # เปลี่ยนเป็น URL จริง
JOB_CHECK_INTERVAL = 2  # ตรวจสอบงานทุก 10 วินาที

# 👉 ใส่ ngrok URL ของ backend main.py (port 8000) สำหรับส่งไฟล์
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
GPIO.setup(LIMIT_SWITCH_PIN, GPIO.IN)
GPIO.setup(PWM, GPIO.OUT)
GPIO.setup(INA, GPIO.OUT)
GPIO.setup(INB, GPIO.OUT)
GPIO.setup(relay_pin, GPIO.OUT)
GPIO.output(relay_pin, GPIO.HIGH)

# === MOTOR CONTROL FUNCTIONS ===
def pull_down():
    GPIO.output(PWM, 10)
    GPIO.output(INA, GPIO.HIGH)
    GPIO.output(INB, GPIO.LOW)

def pull_up():
    GPIO.output(PWM, 10)
    GPIO.output(INA, GPIO.LOW)
    GPIO.output(INB, GPIO.HIGH)

def stop_motor():
    GPIO.output(PWM, 0)
    GPIO.output(INA, GPIO.HIGH)
    GPIO.output(INB, GPIO.LOW)
        
def wait_for_press():
    while True:
        if GPIO.input(LIMIT_SWITCH_PIN) == 0:
            break
        time.sleep(0.1)

def wait_for_release():
    while GPIO.input(LIMIT_SWITCH_PIN) == 0:
        time.sleep(0.01)

# === NEW: STATUS POST FUNCTION ===
def send_status(indexStatus: int):
    """ส่งสถานะการทำงานไปยัง Pond Status API"""
    status_messages = {
        1: "กำลังเริ่มยกยอขึ้น....",
        2: "กำลังเตรียมกล้องถ่ายรูป....",
        3: "ถ่ายสำเร็จ...",
        4: "กรุณารอข้อมูลสักครู่...",
        5: "สำเร็จ!!...."
    }

    message = status_messages.get(indexStatus, "Unknown status")

    try:
        response = requests.post(
            f"{FRONT_API_URL}/api/pond-status/{POND_ID}",
            headers={"Content-Type": "application/json"},
            json={"status": indexStatus, "message": message},
            timeout=5
        )
        if response.status_code == 200:
            log(f"✅ ส่งสถานะ {indexStatus}: {message}")
            return True
        else:
            log(f"❌ ส่งสถานะล้มเหลว {indexStatus}: {response.status_code}")
            return False
    except Exception as e:
        log(f"⚠️ ไม่สามารถส่งสถานะ {indexStatus}: {e}")
        return False


# === CLOUD API FUNCTIONS ===
def check_for_job():
    """ตรวจสอบว่ามีงานจาก cloud หรือไม่"""
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
    """แจ้ง cloud ว่าเสร็จงานแล้ว"""
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

def open_camera(camera_indices=[0, 1, 2]):
    """ลองเปิดกล้องตาม index ที่ส่งมา เลือกกล้องแรกที่อ่าน frame ได้"""
    for idx in camera_indices:
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        time.sleep(2)  # รอให้กล้องพร้อม

        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                log(f"✅ ใช้กล้อง index {idx}")
                return cap
            else:
                log(f"⚠️ กล้อง index {idx} เปิดได้แต่ไม่มีภาพ")
        cap.release()

    raise RuntimeError("ไม่พบกล้องที่ใช้งานได้เลย")

# === MAIN WORK FUNCTION ===
def execute_lift_job(job_data=None):
    """ทำงานยกเชือกและถ่ายรูป"""
    log("🔧 เริ่มทำงานยกเชือก...")
    
    try:
        # === ยกยอขึ้น + ถ่ายรูป ===
        send_status(1)  # ✅ กำลังเริ่มยกยอขึ้น....
        log("⬆️ ยกยอขึ้น")
        start_up_time = time.time()
        pull_up()
        wait_for_press()
        stop_motor()
        time.sleep(3)

        duration_up = time.time() - start_up_time
        log(f"✅ ยกยอขึ้นเสร็จ (ใช้เวลา {duration_up:.2f} วินาที)")

        # === ถ่ายรูป ===
        send_status(2)  # ✅ กำลังเตรียมกล้องถ่ายรูป....
        GPIO.output(relay_pin, GPIO.LOW)
        time.sleep(3)
        log("📷 เตรียมกล้อง...")

        cap = open_camera([0, 1, 2])
        time.sleep(2)

        if not cap.isOpened():
            log("❌ ไม่สามารถเปิดกล้องได้")
            raise RuntimeError("เปิดกล้องไม่ได้")

        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        fps = 20.0
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        video_filename = f"video_pond{POND_ID}_{timestamp}.mp4"
        image_filename = f"shrimp_pond{POND_ID}_{timestamp}.jpg"
        video_path = os.path.join("/home/rwb/depa", video_filename)
        image_path = os.path.join("/home/rwb/depa", image_filename)

        os.makedirs(os.path.dirname(video_path), exist_ok=True)

        log("🎥 เริ่มถ่ายวิดีโอ")
        out = cv2.VideoWriter(
            video_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            (frame_width, frame_height)
        )

        start_time = time.time()
        captured_image = None

        stop_motor()

        while True:
            ret, frame = cap.read()
            if not ret:
                log("❌ ไม่สามารถอ่านภาพจากกล้องได้")
                break

            out.write(frame)

            # Capture still image at 2.5s
            if captured_image is None and time.time() - start_time > 2.5:
                captured_image = frame.copy()
                cv2.imwrite(image_path, captured_image)
                send_status(3)  # ✅ ถ่ายสำเร็จ...
                log(f"📸 ถ่ายภาพนิ่งแล้ว → {image_path}")

            # Stop recording after 5s
            if time.time() - start_time > 5:
                log("⏱️ ครบ 5 วินาที หยุดถ่าย")
                break

        out.release()
        cap.release()

        GPIO.output(relay_pin, GPIO.HIGH)

        # === ยกยอลง ===
        log("⬇️ ยกยอลง")
        pull_down()
        time.sleep(10)  # ยกลง 10 วินาที
        stop_motor()
        log("✅ ยกยอลงเสร็จ")

        # === ส่งไฟล์ไป backend ===
        send_status(4)  # ✅ กรุณารอข้อมูลสักครู่...
        result_data = {
            "status": "success",
            "pond_id": POND_ID,
            "action": "lift_up",
            "timestamp": timestamp,
            "files": {
                "image": image_filename,
                "video": video_filename
            }
        }

        if captured_image is not None:
            log("📤 กำลังส่งภาพและวิดีโอไปยังเซิร์ฟเวอร์...")
            try:
                with open(image_path, "rb") as img_f, open(video_path, "rb") as vid_f:
                    files = [
                        ("files", (image_filename, img_f, "image/jpeg")),
                        ("files", (video_filename, vid_f, "video/mp4"))
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
        else:
            log("⚠️ ไม่มีภาพนิ่งจะส่ง")
            result_data["backend_error"] = "ไม่มีภาพนิ่งจะส่ง"

        send_status(5)  # ✅ สำเร็จ!!....
        return result_data

    except Exception as e:
        log(f"🔥 ERROR ในการทำงาน: {e}")
        return {
            "status": "error",
            "pond_id": POND_ID,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# === HEARTBEAT FUNCTION ===
# Heartbeat ถูกย้ายไปไฟล์ heartbeat.py แยกต่างหาก

# === MAIN LOOP ===
def main():
    log("🔌 เริ่มโปรแกรม controller.py (Cloud Mode)")
    log(f"🌐 Cloud API: {CLOUD_API_URL}")
    log(f"🔄 ตรวจสอบงานทุก {JOB_CHECK_INTERVAL} วินาที")
    log("💓 Heartbeat ทำงานแยกในไฟล์ heartbeat.py")
    
    try:
        while True:
            # ตรวจสอบว่ามีงานหรือไม่
            has_job, job_data = check_for_job()
            
            if has_job:
                log(f"📋 พบงานใหม่: {job_data}")
                
                # ทำงาน
                result = execute_lift_job(job_data)
                
                # แจ้งว่าเสร็จแล้ว
                complete_job(result)
                
                log("✅ งานเสร็จสิ้น รองานใหม่...")
            else:
                log("😴 ไม่มีงาน รอ...")
            
            # รอก่อนตรวจสอบครั้งต่อไป
            time.sleep(JOB_CHECK_INTERVAL)
            
    except KeyboardInterrupt:
        log("🛑 หยุดโปรแกรมโดยผู้ใช้")
    except Exception as e:
        log(f"🔥 ERROR: {e}")
    finally:
        GPIO.cleanup()
        log("🔚 เคลียร์ GPIO แล้ว")

if __name__ == "__main__":
    main()


