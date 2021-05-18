#Code for plant monitoring display on piTFT

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

os.putenv('SDL_VIDEODRIVER', 'fbcon')              #play on piTFT
os.putenv('SDL_FBDEV', '/dev/fb1')
os.putenv('SDL_MOUSEDRV', 'TSLIB')                  #track mouse clicks on piTFT
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# Config Helpers
def read_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
        return data


def write_config(data):
    with open('config.json', 'w') as f:
        json.dump(data, f)


#Set up button 27 (on piTFT) for quitting later
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Script quit button function
def gpio27_callback(channel):
    sys.exit()

#make new button
def new_button(text, x_pos, y_pos, width, height, color):
    left = x_pos - width/2
    top = y_pos - height/2
    button_label = font.render(text, True, color)
    button_rect = button_label.get_rect(center = (x_pos, y_pos))
    pygame.draw.rect(screen, color, (left, top, width, height), 5)
    screen.blit(button_label, button_rect)

#new text label on screen
def new_label(text, x_pos, y_pos, fontsize, color):
    font = pygame.font.Font(None, fontsize)
    text_label = font.render(text, True, color)
    text_rect = text_label.get_rect(center = (x_pos, y_pos))
    screen.blit(text_label, text_rect)

#Check for touch location, return which button was touched
def button_touch(pos):
    global level
    x = pos[0]
    y = pos[1]
    if level == 0:
        if 30 <= x <= 150 and 80 <= y <= 140:
            return 1
        elif 30 <= x <= 150 and 160 <= y <= 220:
            return 3
        elif 190 <= x <= 290 and 80 <= y <= 140:
            return 2
        elif 190 <= x <= 290 and 160 <= y <= 220:
            return 4
        else:
            return 0

#back button
def back_button(pos):
    x = pos[0]
    y = pos[1]
    if 40 <= x <= 140 and 190 <= y <= 230:
        return True
    else:
        return False

def water_button(pos):
    x = pos[0]
    y = pos[1]
    if 180 <= x <= 280 and 190 <= y <= 230:
        return True
    else:
        return False

#photoresistor reading
def light_reading():
    count = 0
    GPIO.setup(light_pin, GPIO.OUT)
    GPIO.output(light_pin, GPIO.LOW)

    time.sleep(0.1)

    while(GPIO.input(light_pin) == GPIO.LOW):
        print(count)
        count += 1
    
    return count 

#DHT reading
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

#detect moisture in soil and turn on water pumps
def p1_auto_pump_water():
    #check soil moisture every [interval] min and water if necessary
    global soil_moisture_1
    global p1_interval

    threading.Timer(p1_interval, p1_auto_pump_water).start()
    
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
    global p2_interval

    threading.Timer(p2_interval, p2_auto_pump_water).start()
        
    if soil_sensor_2.value:
        soil_moisture_2 = "Inadequate"
        GPIO.output(pump_pin_2, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_2, GPIO.HIGH)
    else:
        soil_moisture_2 = "Adequate"

#if user presses water button
def man_pump_water():
    global level

    if level == 3:
        GPIO.output(pump_pin_1, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_1, GPIO.HIGH)
    elif level == 4:
        GPIO.output(pump_pin_2, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_2, GPIO.HIGH)

#display for each level
def display_level():
    global level
    global temp
    global humid
    global p1_sun_threshold 
    global p2_sun_threshold
    global sunlight

    screen.fill(BLACK)
    background_rect = background.get_rect()
    screen.blit(background, background_rect)

    if level == 0:
        new_button("Plant Care", 160, 40, 260, 40, WHITE)
        new_button("Temp", 80, 110, 100, 60, WHITE)
        new_button("Humidity", 240, 110, 100, 60, WHITE)
        new_button("Plant 1", 80, 190, 100, 60, WHITE)
        new_button("Plant 2", 240, 190, 100, 60, WHITE)
    elif level == 1:
        if temp == 0 or isinstance(temp, str):
            temp = "loading"
            new_label("Temperature: " + temp, 160, 110, 30, WHITE)
        else:
            if temp > max_temp:
                new_label(str(temp) + "F: Too hot for plants", 160, 110, 30, RED)
            elif temp < min_temp:
                new_label(str(temp) + "F: Too cold for plants", 160, 110, 30, BLUE)
            else:
                new_label("Temperature: "+ str(temp) + "F", 160, 110, 30, WHITE)
        new_button("Back", 90, 210, 100, 40, WHITE)
    elif level == 2:
        if humid == 0 or isinstance(humid, str):
            humid = "loading"
            new_label("Humidity: " + humid, 160, 130, 30, WHITE)
        else:
            if humid > max_humid:
                new_label(str(humid) + "%: Too high", 160, 110, 30, RED)
            elif humid < min_humid:
                new_label(str(humid) + "%: Too low", 160, 110, 30, BLUE)
            else:
                new_label("Humidity: " + str(humid) + "%", 160, 130, 30, WHITE)
        new_button("Back", 90, 210, 100, 40, WHITE)
    elif level == 3:
        if sunlight < p1_sun_threshold:
            text = "Not Enough Sunlight"
        else:
            text = "Adequate Sunlight"
        new_label(text, 160, 80, 30, WHITE)
        new_label("Soil Moisture: " + soil_moisture_1, 160, 120, 30, WHITE)
        new_button("Back", 90, 210, 100, 40, WHITE)
        new_button("Water", 230, 210, 100, 40, WHITE)
    elif level == 4:
        if sunlight < p2_sun_threshold:
            text = "Not Enough Sunlight"
        else:
            text = "Adequate Sunlight"
        new_label(text, 160, 80, 30, WHITE)
        new_label("Soil Moisture: " + soil_moisture_2, 160, 120, 30, WHITE)
        new_button("Back", 90, 210, 100, 40, WHITE)
        new_button("Water", 230, 210, 100, 40, WHITE)

#web scrape
def web_scrape(plant_type):
    #print("Type in the type of plant: ")
    plant_name = (plant_type).split(" ")
    url = 'https://www.mygarden.org/search?q='
    for i, tok in enumerate(plant_name):
        if (i == len(plant_name)-1):
            url += tok + '&w=plants'
        else:
            url += tok + '+'

    link_req = requests.get(url)
    data = link_req.content
    soup_1 = BeautifulSoup(data, 'html.parser')
    links = [a.get('href') for a in soup_1.find_all(href=True)]
    filt_links = [x for x in links if 'https://www.mygarden.org/plants' in x]

    first_link = filt_links[0]
    req = requests.get(first_link)
    html_page = req.content
    soup_2 = BeautifulSoup(html_page, 'html.parser')
    text = soup_2.find_all(text = True)

    exclude = ['[document]', 'noscript', 'header', 'html', 'meta', 'head', 'input', 'script']

    output = ''

    for x in text: 
        if x.parent.name not in exclude:
            output += '{} '.format(x)
    output = output.lower()

    start_ind = output.index('height')

    try:
        end_ind = output.index('see all varieties')
    except:
        end_ind = output.index('add to my exchange list')

    properties = ['height', 'color', 'soil', 'sunlight', 'ph', 'moisture', 'hardiness']
    prop_dict = dict.fromkeys(properties)

    output = output[start_ind:end_ind]
    output = tokenizer.tokenize(output.lower())

    for i,x in enumerate(output):
        if x in properties:
            min_ind = len(output)
            p_ind = properties.index(x) + 1
            for p in properties[p_ind:len(properties)]:
                try:
                    prop_ind = output.index(p)
                    if prop_ind < min_ind:
                        min_ind = prop_ind
                except:
                    pass
            prop_dict[x] = output[i + 1: min_ind]

    #print(prop_dict)
        
    try:
        ret_sun = " ".join(prop_dict['sunlight'])
    except:
        ret_sun = ""

    try:
        ret_moisture = " ".join(prop_dict['moisture'])
    except:
        ret_moisture = ""

    return ret_sun,ret_moisture

#set up parameters for specific plant types
def plant_param(p1_sun, p1_moisture, p2_sun, p2_moisture):
    global p1_interval
    global p2_interval
    global p1_sun_threshold
    global p2_sun_threshold

    #plant 1 moisture
    if "well drained" in plant1_moisture:
        p1_interval = 60
    elif "moist" in plant1_moisture:
        p1_interval = 45
    else:
        p1_interval = 30
    #plant 1 sun
    if "full" in plant1_sunlight and "partial" in plant1_sunlight:
        p1_sun_threshold = 0.70
    elif "full" in plant1_sunlight:
        p1_sun_threshold = 0.85
    elif "partial" in plant1_sunlight and "shade" in plant1_sunlight:
        p1_sun_threshold = 0.50

    #plant 2 moisture
    if "well drained" in plant2_moisture:
        p2_interval = 60
    elif "moist" in plant2_moisture:
        p2_interval = 45
    else:
        p2_interval = 30
    #plant 2 sun
    if "full" in plant2_sunlight and "partial" in plant2_sunlight:
        p2_sun_threshold = 0.70
    elif "full" in plant2_sunlight:
        p2_sun_threshold = 0.85
    elif "partial" in plant2_sunlight and "shade" in plant2_sunlight:
        p2_sun_threshold = 0.50

#pygame initializations
pygame.init()
screen = pygame.display.set_mode((320, 240))
font = pygame.font.Font(None, 25)
#pygame.mouse.set_visible(False)                     #hide mouse cursor

#Colors
WHITE = (255, 255, 255)
BLACK = (0,0,0)
RED = (255,0,0)
GREEN = (65,169,76)
BLUE = (0,0,255)
YELLOW = (255,255,0)
ORANGE = (255, 165, 0)

#fill screen with BLACK
screen.fill(BLACK)
#background
background = pygame.image.load('plant_background.jpg')
background_rect = background.get_rect()
screen.blit(background, background_rect)

#menu border
pygame.draw.rect(screen, GREEN, (0,0,320,240), 10)

#display level
level = 0

#init buttons
display_level()

#init sunlight
sunlight = 0.0
p1_sun_threshold = 0.1
p2_sun_threshold = 0.9

#init soil
soil_moisture_1 = "Adequate"
soil_moisture_2 = "Adequate"

#init temp/humid
temp = 0.0
humid = 0.0
#min/max for general indoor plants
min_temp = 60
max_temp = 85
min_humid = 30
max_humid = 65

#get initial reading
DHT_reading()
DHT_reading()
DHT_reading()

#set call back for quit button, bouncetime to avoid multiple hits
GPIO.add_event_detect(27, GPIO.FALLING, callback=gpio27_callback, bouncetime=300)
GPIO.add_event_detect(23, GPIO.FALLING, callback=gpio27_callback, bouncetime=300)
GPIO.add_event_detect(22, GPIO.FALLING, callback=gpio27_callback, bouncetime=300)
GPIO.add_event_detect(17, GPIO.FALLING, callback=gpio27_callback, bouncetime=300)

#set up for specific plant1 type
#plant 1
config = read_config()
plant1 = config["1"]["type"]
print(plant1)
if plant1 != "":
    try:
        plant1_sunlight, plant1_moisture = web_scrape(plant1)
    except:
        plant1_sunlight = 0.6
        plant1_moisture = "well drained"

#plant 2
plant2 = config["2"]["type"]
print(plant2)
if plant2 != "":
    try:
        plant2_sunlight, plant2_moisture = web_scrape(plant2)
    except:
        plant2_sunlight = 0.6
        plant2_moisture = "well drained"

plant_param(plant1_sunlight, plant1_moisture, plant2_sunlight, plant2_moisture)

#thread for water pumps
p1_auto_pump_water()
p2_auto_pump_water()

timer = 0

#main loop
while True:
    t_h = DHT_reading()
    if t_h != "error":                                          #sometimes DHT will throw error
        temp = round(t_h[0], 2)
        humid = round(t_h[1], 2)
        sunlight = ldr.value
    if level == 0:
        for event in pygame.event.get():
            if event.type is MOUSEBUTTONDOWN:
                pos = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
                button_num = button_touch(pos) 
                level = button_touch(pos)
                display_level()
            if event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()     																		
    elif level == 1:

        for event in pygame.event.get():
            if event.type is MOUSEBUTTONDOWN:
                pos = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
                if back_button(pos):
                    level = 0
                display_level()
            if event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()  
    
    elif level == 2:
        for event in pygame.event.get():
            if event.type is MOUSEBUTTONDOWN:
                pos = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
                if back_button(pos):
                    level = 0
                display_level()
            if event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()  

    elif level == 3 or level == 4:
        for event in pygame.event.get():
            if event.type is MOUSEBUTTONDOWN:
                pos = (pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])
                if back_button(pos):
                    level = 0
                display_level()
                if water_button(pos):
                    man_pump_water()
            if event.type == KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit() 
    
    # Update Database
    if timer > 1000:
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
        timer = 0


    pygame.display.flip()
    timer += 1

GPIO.cleanup()
