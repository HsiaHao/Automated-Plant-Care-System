# import the necessary packages
import cv2
import numpy as np

img = cv2.imread("./photos/test_plant1.jpg")

brown = [(10, 100, 20), (20, 255, 200)]
green = [(36, 25, 25), (86, 255, 255)]

hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
mask = cv2.inRange(hsv, green[0], green[1])
mask2 = cv2.inRange(hsv, brown[0], brown[1])

cv2.imshow("img", mask)
cv2.waitKey(0)

print(cv2.countNonZero(mask), cv2.countNonZero(mask2))

imask = mask>0
green = np.zeros_like(img, np.uint8)
green[imask] = img[imask]

res = np.hstack((green, img))

cv2.imshow("img", res)
cv2.waitKey(0)