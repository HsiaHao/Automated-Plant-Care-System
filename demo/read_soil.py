import RPi.GPIO as GPIO
import os
import sys
import time
import pygame
from pygame.locals import *                         #for event mouse variables
from gpiozero import LightSensor, DigitalInputDevice
import board
import json
import adafruit_dht
import threading
from bs4 import BeautifulSoup
import requests
from nltk.tokenize import TreebankWordTokenizer, RegexpTokenizer
try:
    import urllib.request as urllib2
except ImportError:
    import urllib2

#set pin mode to BCM
GPIO.setmode(GPIO.BCM)

#GPIO IN (piTFT buttons)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Tokenizer
tokenizer = RegexpTokenizer(r'\w+')

#Light Sensor Setup
light_pin = 5
ldr = LightSensor(light_pin)

#DHT Sensor Setup
dhtDevice = adafruit_dht.DHT22(board.D4, use_pulseio=False)

#Soil Sensor Setup
soil_pin_1 = 19
soil_sensor_1 = DigitalInputDevice(soil_pin_1)

soil_pin_2 = 16
soil_sensor_2 = DigitalInputDevice(soil_pin_2)

#Relay Setup
pump_pin_1 = 21
GPIO.setup(pump_pin_1, GPIO.OUT)
GPIO.output(pump_pin_1, GPIO.HIGH)

pump_pin_2 = 20
GPIO.setup(pump_pin_2, GPIO.OUT)
GPIO.output(pump_pin_2, GPIO.HIGH)

#detect moisture in soil and turn on water pumps
def p1_auto_pump_water():
    #check soil moisture every [interval] min and water if necessary
    global soil_moisture_1
    print(soil_sensor_1.value)
    if soil_sensor_1.value:
        soil_moisture_1 = "Inadequate"
        GPIO.output(pump_pin_1, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_1, GPIO.HIGH)
    else:
        soil_moisture_1 = "Adequate"
    
#detect moisture in soil and turn on water pumps
def p2_auto_pump_water():
    #check soil moisture every [interval] min and water if necessary
    global soil_moisture_2

    if soil_sensor_2.value:
        soil_moisture_2 = "Inadequate"
        GPIO.output(pump_pin_2, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_2, GPIO.HIGH)
    else:
        soil_moisture_2 = "Adequate"

while True:
    p1_auto_pump_water()
    time.sleep(2)