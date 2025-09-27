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
    close_start = None
    while True:

        if channel.voltage <= 0:
            if close_start is None:
                close_start = time.time()
            elif time.time() - close_start >= 0.2:
                log(f"📏 ระยะ {distance:.2f} cm <= {DISTANCE_LIMIT} cm → เจอวัตถุใกล้นานเกิน 1 วินาที หยุด")
                break
        else:
            close_start = None
        print(channel.voltage)
        time.sleep(0.1)
wait_for_press()
