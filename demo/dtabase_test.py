import RPi.GPIO as GPIO
import os
import sys
import time                     #for event mouse variables
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

import sqlite3 as lite
import sys

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

#DHT Reading
def DHT_reading():
    try:
        # Print the values to the serial port
        temperature_c = dhtDevice.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dhtDevice.humidity
        return (temperature_f, humidity)
    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going        
        return "error"
    except Exception as error:
        #dhtDevice.exit()
        return "error"

# Update Database
for x in range(10):
    t_h = DHT_reading()
    if t_h != "error":                                          #sometimes DHT will throw error
        temp = round(t_h[0], 2)
        humid = round(t_h[1], 2)
        sunlight = ldr.value
        DB_NAME = './database/sensorData.db'
        TABLE_NAME = 'PlantTable'
        conn = lite.connect(DB_NAME)
        curs = conn.cursor()
        query = "INSERT INTO {} values({}, datetime('now'), {}, {}, {})".format(TABLE_NAME, 1, temp, humid, sunlight)
        query2 = "INSERT INTO {} values({}, datetime('now'), {}, {}, {})".format(TABLE_NAME, 2, temp, humid, sunlight)

        if temp != None and humid != None:
            curs.execute(query)
            curs.execute(query2)
        conn.commit()
        conn.close()

        print("Reading: ", temp, humid, sunlight)
    