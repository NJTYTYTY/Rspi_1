import time
import os
import json
from datetime import datetime
import RPi.GPIO as GPIO

PWM = 12
INA = 23
INB = 24


GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(PWM, GPIO.OUT)
GPIO.setup(INA, GPIO.OUT)
GPIO.setup(INB, GPIO.OUT)

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
    
pull_down()
time.sleep(5)
stop_motor()
#time.sleep(5)
#pull_down()
#time.sleep(4)
#stop_motor()
