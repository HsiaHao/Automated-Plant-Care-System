import picamera     # Importing the library for camera module
from time import sleep  # Importing sleep from time library to add delay in program
from picamera.array import PiRGBArray
import cv2

camera = picamera.PiCamera()
camera.resolution = (640, 480)
camera.start_preview()
sleep(10)
camera.stop_preview

# Take a photo
rawCapture = PiRGBArray(camera)
sleep(0.1)
camera.capture(rawCapture, format="bgr")
image_1 = rawCapture.array
cv2.imwrite("./photos//test_plant1.jpg", image_1)