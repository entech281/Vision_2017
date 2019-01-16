"""
    Here are some classes we can use to make the code a little easier/more flexible
    TODO: split them out
"""
import time,cv2,math,logging
import numpy as np
from data import ControlPosition,Constants
import os.path,shutil
import itertools

log = logging.getLogger('Recognizer')

def estimated_width_between_targets(target_width):
    return Constants.CENTER_GUESS_CONST*target_width

INFINITY=-99999

class TargetRecognizer(object):
    """
        Target Recognizer accepts a bunch of contours, and
        should provide a list of recognized targets.

        The class is a single object so that we can provide easy access to the targets,
        contours, and other results of processing all at once

        It also contemplates the idea that we might use information from past loops to recognize
    """
    POSITION_NOT_FOUND = ControlPosition(distance=0,direction=0,found=False,num_targets=0)

    def __init__(self,center,settings):
        self.settings = settings
        self.center = center
        self.size = (self.center[0] * 2, self.center[1] * 2 )
        self.target_contours = []
        self.not_target_contours = []     
        self.position = TargetRecognizer.POSITION_NOT_FOUND        
        self.rejectNumber = 0 
        self.filterY = settings.top_filter_percent * self.size[1]
        if os.path.exists(Constants.DEBUG_IMG_DIR):
           shutil.rmtree(Constants.DEBUG_IMG_DIR)
        os.makedirs(Constants.DEBUG_IMG_DIR)
        

    def report_reject(self,reason,img):
        #log.info("rejected %s" % reason )
        if Constants.ENABLE_REJECT_DEBUG:
           self.rejectNumber += 1

           new_image = cv2.putText(img,"R: " + reason ,(5,20),cv2.FONT_HERSHEY_PLAIN,1.0,(255,255,255 ),1 )
           cv2.imwrite(os.path.join(Constants.DEBUG_IMG_DIR,"rejected-%d.jpg" % self.rejectNumber) ,new_image)

    def select_contours(self,targets):
        for t in targets:
            self.target_contours.append(t["contour"])
    
    def process_contours(self,contours,img): 
        self.target_contours = []
        identified_targets = self.filter_targets(contours,img) 

        selected_targets = self.select_targets(identified_targets)
        
        number_of_targets = len(selected_targets)

        #default is position not found
        self.position = TargetRecognizer.POSITION_NOT_FOUND
        
        if number_of_targets == 1:
            if Constants.ACCEPT_ONE_TARGET:

               target = selected_targets[0]
               target_top = target["top"]
               target_width= target["width"]
               target_center_x = target["center_x"]
            
               distance = self.compute_distance(target_width)
               
               #tricky. if there is enough room on the screen to see where the _other_ 
               #side of the target would be, we know it must be opposite
               #we know that we can safely assume the position when we see only one target
               estimated_center_dist = estimated_width_between_targets(target_width)
               width_between_targets = estimated_center_dist - target_width

               screen_center_x = self.size[0] / 2.0

               guessed_center = 0
               can_guess=False
               if target_center_x >= screen_center_x:
                   guessed_center = target_center_x + ( estimated_center_dist/2.0)
                   can_guess = ( target_center_x - width_between_targets > 0 )
               else:
                   guessed_center = target_center_x - (estimated_center_dist/2.0)
                   can_guess = ( target_center_x + width_between_targets < self.size[0] )

               log.debug("Estimated target center dist = %d, width= %d, guessed=%d " % (estimated_center_dist, target_width,guessed_center) ) 

               if can_guess:
                  direction = self.compute_direction(target_width,guessed_center)
                  self.position =  ControlPosition(distance=distance, direction=direction, found=True,num_targets=1)
                  self.select_contours([target])
                            
        elif number_of_targets == 2:
            target1 = selected_targets[0]
            target2 = selected_targets[1]
            avg_top = ( target1["top"] + target2["top"] ) / 2.0
            avg_width = ( target1["width"] + target2["width"])/ 2.0
            max_width = max( target1["width"] ,target2["width"])

            width_between_targets = abs ( target1["center_x"] - target2["center_x"] )

            log.debug("Widths: target1= %d, target2=%d" % ( target1['width'], target2['width']) )

            center_between_targets = (target1["center_x"] + target2["center_x"]) / 2.0

            log.debug("Avg Width: %d, center= %d " % ( avg_width, center_between_targets ))
            log.debug("Avg Top: %d" % avg_top )
            log.debug("Center Width %d " % center_between_targets ) 
            log.debug("Width Between Target Centers= %d" % width_between_targets )
            if width_between_targets < Constants.TARGET_MAX_SPACING_FACTOR  * avg_width:
               distance = self.compute_distance(avg_width)
               direction = self.compute_direction(avg_width,center_between_targets)

               if distance != INFINITY and direction != INFINITY:
                  self.position =  ControlPosition(distance=distance, direction=direction, found=True,num_targets=2)
                  self.select_contours([target1,target2])


    def compute_direction(self,target_width, estimated_center_x):
        """
            direction is proportional to the number of inches 
            we are away from the centerline.
        """
        screen_center = self.size[0] / 2.0
        #computes the direction given a target width value
        #the assumption we make here is that a single target might 
        # have the other buddy off screen
        log.debug("Computing Distance, width=%d, estimated_center=%d" % (target_width, estimated_center_x ) )
        if target_width > 0:
           return Constants.DIRECTION_SCALE / target_width * ( estimated_center_x - screen_center )
        else:
           return INFINITY

    def compute_distance(self,avg_target_width):
        d = float(avg_target_width) / self.size[0]
        if avg_target_width >0:
           return Constants.DISTANCE_SCALE / avg_target_width
        else:
           return INFINITY

    def select_targets(self,possible_targets):
        """
            Accepts a list of targets, and selects the best pair.
            The best pair will have a very small difference in horizontal centers,
            and the distance between the centers in the x direction in the realm of the guess
        
        """
        if len(possible_targets) < 2:
            return possible_targets
        
        combinations = []
        for first,second in itertools.combinations(possible_targets,2):
            dx = abs(first['center_x'] - second['center_x'])
            dy = abs(first['center_y'] - second['center_y'])
            avg_width = ( first['width'] + second['width'] ) / 2.0

            def targets_are_about_the_same_width(width1, width2):
               return True
               if width1/width2 > Constants.TARGET_MAX_WIDTH_FACTOR or width2/width1 > Constants.TARGET_MAX_WIDTH_FACTOR:
                   return False
 
               return True
            estimated_center_dist = estimated_width_between_targets(avg_width)

            if targets_are_about_the_same_width(first['width'], second['width']):
               combinations.append ({
                 'first': first,
                 'second': second,
                 'xError': abs(dx  - estimated_center_dist ),
                 'yError': dy
               })

        
        #sort first by closest vertical error, then by closest horizontal error
        def getKey(item):
            return math.pow( item['yError'],2) + math.pow( item['xError'],2)
        
        sorted_combinations = sorted(combinations,key=getKey)
        if len(sorted_combinations) > 0:
            return [ sorted_combinations[0]["first"], sorted_combinations[0]["second"] ]
        else:
            #if there are no attractive pairs after searching through, give up
            return []
    
        
    def filter_targets(self,list_of_contours,img):
        """ 
           reject targets that do not appear to be the right shape.
           this is a pre-processing step
        """
        num_contours = len(list_of_contours)
        log.debug("%d input contours" % num_contours )


        #phase 1: filter out invalid targets
        #possible targets make it to the next phase
        possible_targets = []

        for contour in list_of_contours:
            perimeter = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour,self.settings.contour_length * perimeter, True)
            x,y,width,height = cv2.boundingRect(contour)
            centerx = x + (width / 2.0)
            centery = y + (height / 2.0)
            log.debug("Center Size=%d" % self.size[1] )
            num_vertices = len(approx)

            if centery <= self.filterY:
                log.debug("Rejected: Too High up: centery=%d, imagecenter=%d" % ( centery, self.size[1] ))
                continue

            accepted = False
            if num_vertices > 3 and num_vertices < 8:
                approx_points = approx.tolist()
                #vertex_error = TargetRecognizer.vertex_error(approx_points)
                aspect_ratio = height / width
                area = height * width * 1.0

                if aspect_ratio > 0.2 and aspect_ratio < 5.0:
                    if area > 30.0:
                       accepted = True
                       log.debug("Accepted, Area=%0.2f, w=%d, h=%d, Vertices=%d, AR=%0.2f, centerx=%d, centery=%d" % (area,width,height,num_vertices, aspect_ratio,centerx,centery ) )
                       possible_targets.append({
                          'width': width,
                          'height' : height,
                          'center_x': centerx,
                          'center_y': centery,
                          'top': y + height,
                          'ar': aspect_ratio,
                          'vertices': num_vertices,
                          #'vertex_error': vertex_error,
                          'area': area,
                          'contour': contour
                          }) 
                    else:
                         self.report_reject("Rejected: too small area  %0.2f " % area, img )
                else:       
                   self.report_reject("Rejected: AR = %0.2f" % aspect_ratio, img )
            else:
               self.report_reject("Rejected: Vertex Count = %d" % num_vertices, img )


        log.debug("%d possible targets. " % len(possible_targets))

        return possible_targets

 

