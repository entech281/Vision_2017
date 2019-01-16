# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import cv2
import time
import numpy as np
import web
import logging
import fractions

from recognizer import TargetRecognizer
from timer import Timer,RateTimer,FpsTimer

from reporters import TestTargetPositionReporter,NetworkTablesPositionReporter
from data import VisionData,VisionSettings,ControlPosition,Constants
from imgwriter import ImageWriter
from framereader import FrameReader
import multiprocessing

log = logging.getLogger('Vision')

#
# these cannot be changed after program startup
#
# Applicable modes for the V2 camera:
#
#   Resolution  Aspect Ratio    Framerates          Video   Image   FoV         Binning
#1   1920x1080   16:9           1/10 <= fps <= 30   x               Partial     None
#2   3280x2464   4:3            1/10 <= fps <= 15   x       x       Full        None
#3   3280x2464   4:3            1/10 <= fps <= 15   x       x       Full        None
#4   1640x1232   4:3            1/10 <= fps <= 40   x               Full        2x2
#5   1640x922    16:9           1/10 <= fps <= 40   x               Full        2x2
#6   1280x720    16:9           40 < fps <= 90      x               Partial     2x2
#7   640x480     4:3            40 < fps <= 90      x               Partial     2x2
#see https://picamera.readthedocs.io/en/release-1.12/fov.html for camera mode details


#
# These can be changed after startup
#
settings = VisionSettings()
settings.read_defaults()
data = VisionData()


def create_camera():

   camera = PiCamera(resolution=Constants.CAPTURE_RESOLUTION,framerate=Constants.CAMERA_FRAMERATE)
   #camera.sensor_mode=CAMERA_MODE
   time.sleep(0.2)
   print ( "Camera Resolution=" + str(camera.resolution))
   time.sleep(1.0)
   
   #exposure modes:
   #night, auto, off, backlight, spotlight, sports, snow, beach, verylong, fixedfps,
   #antishake, fireworks
   camera.exposure_mode = 'off'
   camera.awb_mode = 'off'   
   camera.awb_gains=(settings.red_gain,settings.blue_gain)
   camera.shutter_speed = settings.shutter_speed
   log.info ('Camera Initialized...')
   log.info ("Camera Details")
   log.info ("**************************")
   log.info ("Resolution=" + str(camera.resolution))
   log.info ("Framerate=" + str(camera.framerate ))
   log.info ("SensorMode=" + str(camera.sensor_mode ))
   log.info ("awb_mode=" + str(camera.awb_mode ))
   log.info ("exposure_mode=" + str(camera.exposure_mode ))
   log.info ("AWB Gains=" + str(camera.awb_gains) )
   return camera
   


def draw_contours ( image, target_contours, not_target_contours):

    #resize the contours back up
    new_image = image
    scaled_contours = [ settings.analysis_scale * t for t in target_contours ]
    new_image = cv2.drawContours(new_image, scaled_contours, -1, Constants.RECOGNIZED_TARGET_COLOR, 2)
    
    if settings.display_unrecognized_contours:
        scaled_nontarget_contours = [ settings.analysis_scale * t for t in not_target_contours ]
        new_image = cv2.drawContours(new_image, scaled_nontarget_contours, 
            -1, Constants.UNRECOGNIZED_CONTOUR_COLOR, 1)

    return new_image

def annotate_image( image, fps, position ):
    
    RED = (0,0,255)
    GREEN = ( 0,255,0 )
    WHITE = (255,255,255 )
    BLUE = (255,0,0)
    BLACK = (0,0,0)
    fps_txt = "%0.0f fps" % ( fps )

    new_image = cv2.rectangle(image,(0,0),(130,10),BLACK, cv2.FILLED ) 

    position_txt_color = None
    if position.found:
        position_txt_color = GREEN
    else:
        position_txt_color = RED
    new_image = cv2.putText(new_image,str(position),(1,10),
        cv2.FONT_HERSHEY_PLAIN,0.6,position_txt_color,1 )

    return new_image

def compute_threshold_image( image ):

    filtered = image
    if settings.erode_diameter > 0:
        d = settings.erode_diameter
        kernel = np.ones((d,d),np.uint8)
        filtered = cv2.erode(filtered, kernel, iterations=2)
        filtered = cv2.dilate(filtered, kernel, iterations=2)    


    lower_range = np.array(settings.lower_filter)
    upper_range = np.array(settings.upper_filter)

    filtered = cv2.cvtColor(filtered,cv2.COLOR_BGR2HSV)

    if settings.blur_diameter > 0:
        if settings.blur_diameter % 2 == 0:
           settings.blur_diameter += 1
        blur_diameter = settings.blur_diameter
        filtered = cv2.GaussianBlur(filtered,(blur_diameter,blur_diameter),0)

    filtered = cv2.inRange(filtered,lower_range, upper_range)

    return filtered

def is_valid_image(image):
    if image is not None and len(image) > 0 :
       if np.count_nonzero(image) > 0:
           return True

    return False

def update_camera_settings(settings, camera):
    #todo: do this more elegantly
    #basically says camera needs to be able to be told when to reload settingss
    if camera.shutter_speed != settings.shutter_speed:
        camera.shutter_speed = settings.shutter_speed

    (rg_fraction, bg_fraction) = camera.awb_gains
    (rg_float, bg_float) = ( float(rg_fraction), float(rg_fraction) )
    if abs( rg_float - settings.red_gain) > 0.01 or abs(bg_float - settings.blue_gain) > 0.01:
        camera.awb_gains = ( settings.red_gain, settings.blue_gain)    

def main():
    camera = create_camera()
    frame_reader = FrameReader(camera,Constants.CAMERA_RESOLUTION)

    timer = Timer(autoReportInterval=50)

    fps_timer = FpsTimer(fps=Constants.WEB_FRAME_RATE)

    half_width = settings.analysis_scale*2.0
    center = ( Constants.CAMERA_RESOLUTION[0]/half_width, Constants.CAMERA_RESOLUTION[1]/half_width) 

    recognizer = TargetRecognizer(center ,settings)
    position_reporter = NetworkTablesPositionReporter()
    
    #so that we can share this and update it from the web
    log.info ("Starting Webserver")
    web.start_server(settings, data)
    log.info( "Web Server Started")

    frame_reader.start()
    log.info("Frame Reader Thread Started")
    rate_timer = RateTimer("Image Process",200)
    sequence = 0
    try:
        while True:
            sequence += 1
            timer.start_loop()

            update_camera_settings(settings,camera)
            
            # grab the raw NumPy array representing the image - this array
            # will be 3D, representing the width, height, and # of channels

            image = frame_reader.read()
            if not is_valid_image(image):
               log.debug('Skipping invalid frame.')
               continue

            rate_timer.tick()

            image = cv2.cvtColor(image,cv2.COLOR_YUV2BGR)
            
            timer.start("threshold")
            threshold_image = compute_threshold_image(image) 
            timer.end("threshold")

            timer.start("find_contours")
            contours = cv2.findContours(threshold_image,cv2.RETR_EXTERNAL ,cv2.CHAIN_APPROX_SIMPLE)[1] 
            timer.end("find_contours")

            timer.start("process_contours")
            recognizer.process_contours(contours,threshold_image)
            timer.end("process_contours")
            
            position = recognizer.position
            position_reporter.report_position(recognizer.position)

            if settings.display_mode == VisionSettings.DISPLAY_MODE_IMAGE:
                display_image = image
                display_image = draw_contours(display_image,recognizer.target_contours, recognizer.not_target_contours)
            elif settings.display_mode == VisionSettings.DISPLAY_MODE_THRESH:
                display_image = threshold_image
            else:
                display_image = image


            timer.start("annotate")
            display_image = annotate_image(display_image,timer.get_fps(),position)
            timer.end("annotate")

            timer.start("write")
            if fps_timer.should_tick():
               cv2.imwrite(Constants.OUTPUT_FILE,display_image)
            timer.end("write")
            
            #update data for the web
            data.distance =  position.distance
            data.direction = position.direction
            data.found = position.found
            data.frame_rate = timer.get_fps()
            data.timings = {
               'frameread': frame_reader.rate_timer.get_rate(),
               'network' : position_reporter.timer.get_rate(),
               'process' : rate_timer.get_rate()
            }

            # clear the stream in preparation for the next frame
            #raw_capture.truncate(0)
            
            timer.end_loop()

        
    finally:
        #stop frame reader
        frame_reader.stop()

        #stop webserver  
        web.stop_server()

        #stop reporter
        position_reporter.shutdown()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(name)-10s]: %(asctime)s %(levelname)s %(message)s')
    main()



    
