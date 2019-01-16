# import the necessary packages
from picamera.array import PiRGBArray,PiYUVArray
from picamera import PiCamera
from threading import Thread
import cv2
from timer import RateTimer

OUTPUT_FILE='/run/camera/vision.jpg'

class FrameReader:
    def __init__(self, camera,output_resolution):
        # initialize the camera and stream
        self.camera = camera
        self.rawCapture = PiYUVArray(self.camera, size=output_resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            #storing yuv here moves the transform to the processing thread,
            #which is slightly more efficient in this case
            #format="bgr", use_video_port=True,resize=output_resolution)
            format="yuv",use_video_port=True,resize=output_resolution)
 
        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.stopped = False
        self.rate_timer = RateTimer("FrameReader",200)

    def start(self):
        # start the thread to read frames from the video stream
        Thread(target=self.update, args=()).start()
        return self
 
    def update(self):
        # keep looping infinitely until the thread is stopped
        

        for f in self.stream:
            self.rate_timer.tick()
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            self.frame = f.array
            #cv2.imwrite(OUTPUT_FILE,self.frame)
            self.rawCapture.truncate(0)
 
            # if the thread indicator variable is set, stop the thread
            # and resource camera resources
            if self.stopped:
                self.stream.close()
                self.rawCapture.close()
                self.camera.close()
                return

    def read(self):
        # return the frame most recently read
        return self.frame
 
    def stop(self):
        # indicate that the thread should be stopped
        self.stopped = True