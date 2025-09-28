import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
SENSOR_PIN = 17
GPIO.setup(SENSOR_PIN, GPIO.IN)

try:
    while True:
        if GPIO.input(SENSOR_PIN) == 0:
            print("Sensor HIGH")
        else:
            print("Sensor LOW")
        time.sleep(0.5)
except KeyboardInterrupt:
    GPIO.cleanup()
    
