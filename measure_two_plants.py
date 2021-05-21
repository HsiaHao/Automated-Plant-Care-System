import argparse
import imutils.contours
import cv2
import numpy as np
from picamera import PiCamera
from picamera.array import PiRGBArray
from time import sleep
import sqlite3 as lite
import sys

# command: python3 measure.py -w 16
# When executing this program, it will stop and show you the results.
# Press any key to contrinue.
# -w: the height of the reference object
parser = argparse.ArgumentParser(description='Object height measurement')

parser.add_argument("-w", "--width", type=float, required=True,
                    help="width of the left-most object in the image")
args = vars(parser.parse_args())

#Use the a photo from camera or an exist image
#True: Image / False: Camera
image_or_camera = True

if image_or_camera==False:
    #Take a photo
    camera = PiCamera()
    rawCapture = PiRGBArray(camera)
    sleep(0.1)
    camera.capture(rawCapture, format="bgr")
    image_1 = rawCapture.array
    cv2.imshow("Image", image_1)
    cv2.waitKey(0)
else:
    image = cv2.imread("resize_plants.jpg")

if image is None:
    print('Could not open or find the image:')
    exit(0)

#####   Color Detection    #####

# HSV color range
brown = [(10, 100, 20), (20, 255, 200)]
green = [(36, 25, 25), (86, 255, 255)]

# Detect green and brown color
hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, green[0], green[1])
mask2 = cv2.inRange(hsv, brown[0], brown[1])

cv2.imshow("img", image)
cv2.waitKey(0)

print("Green and Brown pixels:",cv2.countNonZero(mask), cv2.countNonZero(mask2))

# count the ratio green_pixels / (green_pixels + brown_pixels)
green_color = cv2.countNonZero(mask)
brown_color = cv2.countNonZero(mask2)
ratio = green_color / (green_color + brown_color)
print('ratio: ', ratio)

#show thr result images
imask = mask>0
green_img = np.zeros_like(image, np.uint8)
green_img[imask] = image[imask]

imask = mask2>0
brown_img = np.zeros_like(image, np.uint8)
brown_img[imask] = image[imask]

res = np.hstack((image, green_img))
cv2.imshow("img", res)
cv2.waitKey(0)
res = np.hstack((image, brown_img))
cv2.imshow("img", res)
cv2.waitKey(0)

#####   Measure plant height    #####

# Cover to grayscale and blur
greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
greyscale = cv2.GaussianBlur(greyscale, (7, 7), 0)

# Detect edges and close gaps
canny_output = cv2.Canny(greyscale, 25, 30)
canny_output = cv2.dilate(canny_output, None, iterations=1)
canny_output = cv2.erode(canny_output, None, iterations=1)
canny_output = cv2.GaussianBlur(canny_output, (9, 9), 0)

res = np.hstack((greyscale, canny_output))
cv2.imshow("Image", res)
cv2.waitKey(0)

# Get the contours of the shapes, sort l-to-r and create boxes
_, contours, _ = cv2.findContours(canny_output, cv2.RETR_EXTERNAL,
                                  cv2.CHAIN_APPROX_SIMPLE)
if len(contours) < 3:
    print("Couldn't detect three or more objects")
    exit(0)

(contours, _) = imutils.contours.sort_contours(contours)
contours_poly = [None]*len(contours)  
boundRect = [None]*len(contours)
for i, c in enumerate(contours):
    contours_poly[i] = cv2.approxPolyDP(c, 3, True)
    boundRect[i] = cv2.boundingRect(contours_poly[i])

output_image = image.copy()
mmPerPixel = args["width"] / boundRect[0][3]
highestRect = 1000
lowestRect = 0

#initial plant1,2 measure values
plant1_highrect = 1000
plan1_lowrect = 0
plant2_highrect = 1000
plan2_lowrect = 0

# the x coordinate seperate two plants
image_divide_point = 300

print("number of contours", len(contours))
valid_contour = 0
for i in range(1, len(contours)):
    # print("bound coordinate: ",int(boundRect[i][0]), int(boundRect[i][1]))
    # ignore too small objects
    if boundRect[i][2] < 50 or boundRect[i][3] < 50:
        continue
    # print("The Object is at",boundRect[i][2],boundRect[i][3])
    valid_contour+=1
    # The first rectangle is our control, so set the ratio
    if highestRect > boundRect[i][1]:
        highestRect = boundRect[i][1]
    if lowestRect < (boundRect[i][1] + boundRect[i][3]):
        lowestRect = (boundRect[i][1] + boundRect[i][3])

    if int(boundRect[i][0])<image_divide_point:
        print("left contours: ",int(boundRect[i][0]), int(boundRect[i][1]))
        if plant1_highrect>boundRect[i][1]:
            plant1_highrect = boundRect[i][1]
        if plan1_lowrect < (boundRect[i][1] + boundRect[i][3]):
            plan1_lowrect = (boundRect[i][1] + boundRect[i][3])
    else:
        print("right contours: ",int(boundRect[i][0]), int(boundRect[i][1]))
        if plant2_highrect>boundRect[i][1]:
            plant2_highrect = boundRect[i][1]
        if plan2_lowrect < (boundRect[i][1] + boundRect[i][3]):
            plan2_lowrect = (boundRect[i][1] + boundRect[i][3])

    # Create a boundary box
    cv2.rectangle(output_image, (int(boundRect[i][0]), int(boundRect[i][1])),
                  (int(boundRect[i][0] + boundRect[i][2]),
                  int(boundRect[i][1] + boundRect[i][3])), (255, 0, 0), 2)
print("valid_contours:", valid_contour)
# Calculate the size of our plant
plantHeight = (lowestRect - highestRect) * mmPerPixel
#print("Plant height is {0:.0f}mm".format(plantHeight))

#First Plant
plantHeight = (plan1_lowrect - plant1_highrect) * mmPerPixel
print("First plant height is {0:.0f}mm".format(plantHeight))

#Second Plant
plantHeight2 = (plan2_lowrect - plant2_highrect) * mmPerPixel
print("Second plant height is {0:.0f}mm".format(plantHeight2))

######### Write height and greenness to database  #########
 DB_NAME = './database/sensorData.db'
 TABLE_NAME = 'CameraTable'
 conn = lite.connect(DB_NAME)
 curs = conn.cursor()
 query = "INSERT INTO {} values({}, datetime('now'), {}, {})".format(TABLE_NAME, 1, plantHeight, ratio)
 query2 = "INSERT INTO {} values({}, datetime('now'), {}, {})".format(TABLE_NAME, 2, plantHeight2, ratio)
 curs.execute(query)
 curs.execute(query2)
 conn.commit()
 conn.close()


# Resize and display the image and show the result
resized_image = cv2.resize(output_image, (360, 640))
cv2.imshow("Image", resized_image)
cv2.waitKey(0)
