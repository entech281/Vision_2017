import cv2
import numpy as np
from picamera.array import PiRGBArray
from picamera import PiCamera

def nothing(x):
    pass

CAMERA_MODE=7
FRAMERATE=60
RESOLUTION= "1280x720"

camera = PiCamera(resolution=RESOLUTION,framerate=FRAMERATE)
#camera.sensor_mode=CAMERA_MODE
#camera.resolution = RESOLUTION
#camera.
#camera.framerate = 32
rawCapture = PiRGBArray(camera)
print ("Camera Details")
print ("**************************")
print ("Resolution=" + str(camera.resolution))
print ("Framerate=" + str(camera.framerate ))
print ("SensorMode=" + str(camera.sensor_mode ))
print ("awb_mode=" + str(camera.awb_mode ))
print ("exposure_mode=" + str(camera.exposure_mode ))

# Creating a window for later use
cv2.namedWindow('filter')

# Starting with 100's to prevent error while masking
h,s,v = 100,100,100

# Creating track bar
cv2.createTrackbar('hl', 'filter',0,179,nothing)
cv2.createTrackbar('sl', 'filter',0,255,nothing)
cv2.createTrackbar('vl', 'filter',0,255,nothing)
cv2.createTrackbar('hu', 'filter',179,179,nothing)
cv2.createTrackbar('su', 'filter',255,255,nothing)
cv2.createTrackbar('vu', 'filter',255,255,nothing)


for f in camera.capture_continuous(rawCapture, format="bgr", use_video_port=False):

    frame = f.array
    #converting to HSV
    hsv = cv2.cvtColor(frame,cv2.COLOR_BGR2HSV)

    # get info from track bar and appy to result
    hl = cv2.getTrackbarPos('hl','filter')
    sl = cv2.getTrackbarPos('sl','filter')
    vl = cv2.getTrackbarPos('vl','filter')

    hu = cv2.getTrackbarPos('hu','filter')
    su = cv2.getTrackbarPos('su','filter')
    vu = cv2.getTrackbarPos('vu','filter')


    # Normal masking algorithm
    lower = np.array([hl,sl,vl])
    upper = np.array([hu,su,vu])

    mask = cv2.inRange(hsv,lower, upper)

    result = cv2.bitwise_and(frame,frame,mask = mask)

    cv2.imshow('filtergi',frame)

    k = cv2.waitKey(5) & 0xFF
    if k == 27:
        break

    rawCapture.truncate(0)

cap.release()

cv2.destroyAllWindows()