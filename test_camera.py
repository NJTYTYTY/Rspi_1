import subprocess
import time
from datetime import datetime
import os

VIDEO_DEVICE = "/dev/video0"
WIDTH = 640
HEIGHT = 360
PIXELFORMAT = "MJPG"
SAVE_DIR = "/home/rwb/depa"
MAX_RETRY = 5
DELAY_RETRY = 1  # วินาที

def log(msg):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}")

def capture_image_v4l2():
    os.makedirs(SAVE_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    image_path = os.path.join(SAVE_DIR, f"test_{timestamp}.jpg")

    for i in range(1, MAX_RETRY + 1):
        try:
            # ตั้งค่า resolution + pixel format
            subprocess.run(
                ["v4l2-ctl", "-d", VIDEO_DEVICE,
                 "--set-fmt-video", f"width={WIDTH},height={HEIGHT},pixelformat={PIXELFORMAT}"],
                check=True
            )

            # capture 1 frame
            result = subprocess.run(
                ["v4l2-ctl", "-d", VIDEO_DEVICE,
                 "--stream-mmap", "--stream-count=1", f"--stream-to={image_path}"]
            )

            if result.returncode == 0:
                log(f"✅ Capture สำเร็จครั้งที่ {i} → {image_path}")
                return image_path
            else:
                log(f"⚠️ Capture ล้มเหลวครั้งที่ {i}, retry อีกครั้งหลัง {DELAY_RETRY}s")
                time.sleep(DELAY_RETRY)
        except subprocess.CalledProcessError as e:
            log(f"⚠️ Error ครั้งที่ {i}: {e}")
            time.sleep(DELAY_RETRY)

    raise RuntimeError("❌ Capture ไม่สำเร็จแม้ retry หลายครั้ง")

if __name__ == "__main__":
    capture_image_v4l2()
