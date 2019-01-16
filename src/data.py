import json,logging
import os.path
log = logging.getLogger('Recognizer')

class Constants:
    #used to estimate distance based on target width. units are pixel-inches
    #needs tuning
    DISTANCE_SCALE=740

    #estimate lateral shift based on target width, units are pixel-inches
    #needs tuning
    DIRECTION_SCALE=2.5

    DEBUG_IMG_DIR='/tmp/rj'
    ENABLE_REJECT_DEBUG=False

    #how far apart, as a multiple of target width, is far enough to reject them as a pair?
    TARGET_MAX_SPACING_FACTOR=6
    
    #how different can the width of two targets be in order not to be a pair?
    TARGET_MAX_WIDTH_FACTOR=1.5

    #should we automatically reject a single target? or should we assume its pair is off frame?
    ACCEPT_ONE_TARGET=True

    #how far apart should be the centers, based on a known target width
    CENTER_GUESS_CONST=4.125

    POSITION_TABLE="position"
    FOUND_KEY="found"
    DIRECTION_KEY="direction"
    DISTANCE_KEY="distance"
    NUM_TARGETS_KEY="numtargets"
    TEAM_281=281
    UPDATE_RATE_MS=0.010
    PI_SEQUENCE="rpi_sequence"
    RIO_ALIVE="rio_alive"
    RIO_HOST="roborio-281-frc.local"

    
    OUTPUT_FILE='/run/camera/vision.jpg'

    #capturing at a bigger resolution lets us have a wider field of view
    #1640x922 is the widest field of view, but is much slower than 1280x720
    CAPTURE_RESOLUTION = ( 1280,720)
    CAMERA_RESOLUTION= (320,90)

    CAMERA_FRAMERATE = 60
    RECOGNIZED_TARGET_COLOR = ( 255, 0, 0 )
    UNRECOGNIZED_CONTOUR_COLOR = ( 0, 0, 255) 
    WEB_FRAME_RATE=5    
    

class VisionSettings(object):
    DISPLAY_MODE_IMAGE = "IMAGE"
    DISPLAY_MODE_THRESH = "THRESHOLD"
    DEFAULTS_FILE = '/home/pi/vision-defaults.json'
    
    def __init__(self):
        self.lower_filter = [45,0,150]
        self.upper_filter = [65,255,255]
        self.display_threshold = True
        self.analysis_scale = 1
        self.display_mode = VisionSettings.DISPLAY_MODE_IMAGE
        self.blur_diameter = 0
        self.erode_diameter = 2
        self.contour_length = 0.02
        self.display_unrecognized_contours = True
        self.awb_mode = 'off'
        self.exposure = 'off'
        self.shutter_speed = 2500
        self.blue_gain = 1.5
        self.red_gain = 2.5
        self.top_filter_percent=0.1

    def save_defaults(self):
        s = json.dumps(self.__dict__)
        log.warn("Saving Defaults to '%s' : %s" % (VisionSettings.DEFAULTS_FILE, s))
        with open(VisionSettings.DEFAULTS_FILE, "w") as text_file:
            text_file.write(s)

    def read_defaults(self):
        if os.path.isfile(VisionSettings.DEFAULTS_FILE):
            try:
                with open(VisionSettings.DEFAULTS_FILE, "r") as text_file:
                    d = json.load(text_file)
                    self.update_from_dict(d)
            except:
                print ("Error Reading Defaults from '%s'" % VisionSettings.DEFAULTS_FILE)

        

    def update_from_dict(self,d):
        keys = d.keys()
        if 'display_mode' in keys:
            self.display_mode = d['display_mode']

        if 'awb_mode' in keys:
            self.awb_mode = d['awb_mode']

        if 'exposure' in keys:
            self.exposure = d['exposure']

        if 'shutter_speed' in keys:
            s = int(d['shutter_speed'])
            if s > 0:
               self.shutter_speed = s

        if 'red_gain' in keys:
            s = float(d['red_gain'])
            if s > 0:
               self.red_gain = s

        if 'blue_gain' in keys:
            s = float(d['blue_gain'])
            if s > 0:
               self.blue_gain = s
         
        if 'analysis_scale' in keys:
            s = int(d['analysis_scale'])
            if s > 0:
               self.analysis_scale = s

        if 'lower_filter' in keys:
            t = d['lower_filter']
            self.lower_filter = [ int(t[0]), int(t[1]), int(t[2])]

        if 'upper_filter' in keys:
            t = d['upper_filter']
            self.upper_filter = [ int(t[0]), int(t[1]), int(t[2])]

        if 'erode_diameter' in keys:
            self.erode_diameter = int(d['erode_diameter'])

        if 'blur_diameter' in keys:
            self.blur_diameter = int(d['blur_diameter'])


class VisionData(object):
    def __init__(self):
        self.distance = None
        self.direction = None
        self.found = None
        self.frame_rate = 0.0
        self.timings = None


class ControlPosition(object):
    """
        Control output based on the targets
    """
    def __init__(self, distance=0,direction=0,found=False,num_targets=0):
        self.distance = distance
        self.direction = direction
        self.found = found
        self.num_targets = num_targets
       
    def __str__(self):
        return "Dist:%d, Dir:%d, F:%s, #t:%d" % ( self.distance, self.direction, str(self.found), self.num_targets)

if __name__ == "__main__":
    s = VisionSettings()
    j = json.dumps(s.__dict__)
    t = VisionSettings()
    t.__dict__ = json.loads(j)
    
    print( s.__dict__)
    print( t.__dict__)
