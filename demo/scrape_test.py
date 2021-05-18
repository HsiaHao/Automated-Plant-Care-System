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

#set pin mode to BCM
GPIO.setmode(GPIO.BCM)

#GPIO IN (piTFT buttons)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(22, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(23, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#Tokenizer
tokenizer = RegexpTokenizer(r'\w+')

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

    try:
        ret_hardiness = " ".join(prop_dict['hardiness'])
    except:
        ret_hardiness = ""

    return ret_sun,ret_moisture, ret_hardiness

while True:
    print("Type in your plant: ")
    plant_type = str(input())
    sunlight, moisture, hardiness = web_scrape(plant_type)
    print("Sunlight: " + sunlight)
    print("Moisture: " + moisture)
    print("Hardiness: " + hardiness)