import RPi.GPIO as GPIO
import time

relay_pin = 26
GPIO.setmode(GPIO.BCM)
GPIO.setup(relay_pin, GPIO.OUT)

print("Relay ON")
GPIO.output(relay_pin, GPIO.LOW)   # try LOW first
time.sleep(2)

print("Relay OFF")
GPIO.output(relay_pin, GPIO.HIGH)
time.sleep(2)

GPIO.cleanup()
