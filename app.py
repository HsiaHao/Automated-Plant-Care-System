# Temp solution to a python issue...

import picamera     # Importing the library for camera module
from picamera.array import PiRGBArray
from time import sleep  # Importing sleep from time library to add delay in program
import RPi.GPIO as GPIO
import sqlite3 as lite
from flask import Flask, render_template, request, Response, redirect, url_for
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as dates
import base64
from io import BytesIO
import json
import time
import picamera
import cv2
import socket
import io


app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0


# GPIO Setup
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

plant1_pin = 5
plant2_pin = 7

GPIO.setup(plant1_pin, GPIO.OUT)
GPIO.output(plant1_pin, GPIO.LOW)
GPIO.setup(plant2_pin, GPIO.OUT)
GPIO.output(plant2_pin, GPIO.LOW)

# Database Constants
DB_NAME = './database/sensorData.db'
TABLE_NAME = 'PlantTable'

# Relay Setup
pump_pin_1 = 21
GPIO.setup(pump_pin_1, GPIO.OUT)
GPIO.output(pump_pin_1, GPIO.HIGH)

pump_pin_2 = 20
GPIO.setup(pump_pin_2, GPIO.OUT)
GPIO.output(pump_pin_2, GPIO.HIGH)


def man_pump_water(id):

    if id == 1:
        GPIO.output(pump_pin_1, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_1, GPIO.HIGH)
    elif id == 2:
        GPIO.output(pump_pin_2, GPIO.LOW)
        time.sleep(1)
        GPIO.output(pump_pin_2, GPIO.HIGH)


def read_config():
    with open('config.json') as json_file:
        data = json.load(json_file)
        return data


def write_config(data):
    with open('config.json', 'w') as f:
        json.dump(data, f)


def getLatest(id):
    conn = lite.connect(DB_NAME)
    curs = conn.cursor()
    time, temp, hum, light, camera_time, height, greenness = 0, 0, 0, 0, 0, 0, 0
    for row in curs.execute("SELECT * FROM {} WHERE id={} ORDER BY timestamp DESC LIMIT 1".format(TABLE_NAME, id)):
        time, temp, hum, light = str(row[1]), str(
            row[2]), str(row[3]), str(row[4])
    for row in curs.execute("SELECT * FROM {} WHERE id={} ORDER BY timestamp DESC LIMIT 1".format("CameraTable", id)):
        camera_time, height, greenness = str(row[1]), str(
            row[2]), str(row[3])

    conn.close()
    return time, temp, hum, light, camera_time, height, greenness


def getHist(id):
    conn = lite.connect(DB_NAME)
    curs = conn.cursor()
    time_hist = []
    temp_hist = []
    hum_hist = []
    light_hist = []
    for row in curs.execute("SELECT * FROM {} WHERE id={} ORDER BY timestamp LIMIT 10".format(TABLE_NAME, id)):
        time_hist.append(row[1])
        temp_hist.append(row[2])
        hum_hist.append(row[3])
        light_hist.append(row[4])

    camera_time_hist = []
    height_hist = []
    greenness_hist = []
    for row in curs.execute("SELECT * FROM {} WHERE id={} ORDER BY timestamp LIMIT 10".format("CameraTable", id)):
        camera_time_hist.append(row[1])
        height_hist.append(row[2])
        greenness_hist.append(row[3])

    return time_hist, temp_hist, hum_hist, light_hist, camera_time_hist, height_hist, greenness_hist


def getCameraPlots(id):
    fig = Figure()
    FigureCanvas(fig)

    _, _, _, _, camera_time_hist, height_hist, greenness_hist = getHist(id)

    ax1 = fig.add_subplot(3, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)

    # ax = fig.subplots()
    ax1.plot(camera_time_hist, height_hist)
    ax1.set_ylabel("Height")
    ax2.plot(camera_time_hist, greenness_hist)
    ax2.set_ylabel("Greenness")

    fig.autofmt_xdate()

    ax1.set_title("Plant {} Camera Data".format(id))

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data


def getPlots(id):
    fig = Figure()
    FigureCanvas(fig)

    time_hist, temp_hist, hum_hist, light_hist, _, _, _ = getHist(id)

    ax1 = fig.add_subplot(3, 1, 1)
    ax2 = fig.add_subplot(3, 1, 2)
    ax3 = fig.add_subplot(3, 1, 3)

    # ax = fig.subplots()
    ax1.plot(time_hist, temp_hist)
    ax1.set_ylabel("Temperature")
    ax2.plot(time_hist, hum_hist)
    ax2.set_ylabel("Humidity")

    ax3.plot(time_hist, light_hist)
    ax3.set_ylabel("Light")

    fig.autofmt_xdate()

    ax1.set_title("Plant {} Data".format(id))

    # Save it to a temporary buffer.
    buf = BytesIO()
    fig.savefig(buf, format="png")
    # Embed the result in the html output.
    data = base64.b64encode(buf.getbuffer()).decode("ascii")
    return data


@app.route("/", methods=["GET", "POST"])
def index():
    config = read_config()

    # Get form
    if request.method == "POST":
        plant1 = request.form.get("Plant1")
        plant2 = request.form.get("Plant2")
        if plant1 != "":
            config["1"]["type"] = plant1
            write_config(config)
        if plant2 != "":
            config["2"]["type"] = plant2
            write_config(config)

    time1, temp1, hum1, light1, camera_time1, height1, greenness1 = getLatest(
        1)
    time2, temp2, hum2, light2, camera_time2, height2, greenness2 = getLatest(
        2)
    plot1 = getPlots(1)
    plot2 = getPlots(2)
    camera_plot1 = getCameraPlots(1)
    camera_plot2 = getCameraPlots(2)

    # Alerts
    green_alert1 = "Plant 1 is healthy color"
    green_alert2 = "Plant 2 is healthy color"
    if float(greenness1) < 0.8:
        green_alert1 = "Plant 1 is too brown"
    if float(greenness2) < 0.8:
        green_alert2 = "Plant 2 is too brown"

    templateData = {
        'time1': time1,
        'temp1': temp1,
        'hum1': hum1,
        'light1': light1,
        'time2': time2,
        'temp2': temp2,
        'hum2': hum2,
        'light2': light2,
        'camera_time1': camera_time1,
        'height1': height1,
        'greenness1': greenness1,
        'camera_time2': camera_time2,
        'height2': height2,
        'greenness2': greenness2,
        'plot1': plot1,
        'plot2': plot2,
        'camera_plot1': camera_plot1,
        'camera_plot2': camera_plot2,
        'mode1': config["1"]['mode'],
        'mode2': config["2"]['mode'],
        'water1': config["1"]['water'],
        'water2': config["2"]['water'],
        'type1': config["1"]["type"],
        'type2': config["2"]["type"],
        'green_alert1' : green_alert1,
        'green_alert2' : green_alert2
    }
    print(read_config())
    return render_template('index_gpio.html', **templateData)


# Action is water or setting
# Both of which toggle

@app.route("/<plant>/<action>", methods=["GET", "POST"])
def toggle(plant, action):
    config = read_config()

    # Update Config
    # Get form
    if request.method == "POST":
        plant1 = request.form.get("Plant1")
        plant2 = request.form.get("Plant2")
        print(plant1, plant2)
        if plant1 != "":
            config["1"]["type"] = plant1
        if plant2 != "":
            config["2"]["type"] = plant2

    if action == 'mode':
        if config[plant][action] == 'Manual':
            config[plant][action] = 'Automatic'
        else:
            config[plant][action] = 'Manual'
    else:
        print(action)
        print(config[plant][action])
        if config[plant][action] == 'On':
            config[plant][action] = 'Off'
        else:
            config[plant][action] = 'On'

    # Control GPIO
    print("Action, plant: ", action, plant)
    if config[plant][action] == "On":
        man_pump_water(int(plant))
        print("Pumping: ", plant)

    write_config(config)

    return redirect(url_for('index'))


# @app.route("/update")
# def update_photo():
#     camera = picamera.PiCamera()
#     camera.resolution = (640, 480)
#     rawCapture = PiRGBArray(camera)
#     sleep(0.1)
#     try:
#         camera.capture(rawCapture, format="bgr")
#         camera.close()
#         image_1 = rawCapture.array
#         cv2.imwrite("./static//camera_image.jpg", image_1)
#         return redirect(url_for('index'))
#     except:
#         print("Unable to Capture Image")
#         return redirect(url_for('index'))


# No caching at all for API endpoints.
@app.after_request
def add_header(response):
    # response.cache_control.no_store = True
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check = 0, pre-check = 0, max-age = 0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=70, debug=True)
