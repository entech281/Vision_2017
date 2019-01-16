"""
    Here are some classes we can use to make the code a little easier/more flexible
    TODO: split them out
"""
import time,cv2,math,logging
import numpy as np
from data import ControlPosition


DIRECTION_LIMIT=100
DISTANCE_SCALE=100

log = logging.getLogger('Recognizer')

class TargetRecognizer(object):
    """
        Target Recognizer accepts a bunch of contours, and
        should provide a list of recognized targets.

        The class is a single object so that we can provide easy access to the targets,
        contours, and other results of processing all at once

        It also contemplates the idea that we might use information from past loops to recognize
    """
    def __init__(self,center,settings):
        self.settings = settings
        self.center = center
        self.size = (self.center[0] * 2, self.center[1] * 2 )
        self.target_contours = None
        self.not_target_contours = None        
        self.position = None        

    def process_contours(self,contours): 

        (selected, not_selected ) = self.filter_targets(contours)
        self.target_contours = [ s.contour for s in selected ]
        self.not_target_contours = [ s.contour for s in not_selected ]

        log.debug("Selected: %d, not selected: %d" % (len(selected),len(not_selected)) )
        number_of_targets = len(selected)

        POSITION_NOT_FOUND = ControlPosition(distance=0,direction=0,found=False)
        if number_of_targets == 0:
            self.position = POSITION_NOT_FOUND

        elif number_of_targets == 1:
            target = selected[0]
            center_x = target.center[0]

            distance = self.compute_distance(target.width)
            direction = self.compute_direction(target.center[0])
            adjusted_direction = 0.0
            ADJUST_LIMIT = 0.6

            #if only one target, we'll assume we're 'off the page' in the found direction
            #but only if the target is already out to the right

            if direction > DIRECTION_LIMIT*ADJUST_LIMIT:
                adjusted_direction = DIRECTION_LIMIT
            elif direction < DIRECTION_LIMIT*ADJUST_LIMIT*-1.0:
                adjusted_direction = (-1.0) * DIRECTION_LIMIT
            else:
                adjusted_direction = direction


            self.position =  ControlPosition(distance=distance, direction=direction, found=True)
           
        elif number_of_targets == 2:
            target1 = selected[0]
            target2 = selected[1]
            avg_width = ( target1.width + target2.width)/ 2.0

            center_between_targets = (target1.center[0] + target2.center[0]) / 2.0
            log.info("Avg Width: %d, center= %d " % ( avg_width, center_between_targets ))

            distance = self.compute_distance(avg_width)
            direction = self.compute_direction(center_between_targets)
            self.position =  ControlPosition(distance=distance, direction=direction, found=True)


        else:
            self.position = POSITION_NOT_FOUND


    def compute_direction(self,x_value):
        #computes the direction given an x value
        return (x_value - self.center[0]) / self.size[0]* 2.0 * DIRECTION_LIMIT

    def compute_distance(self,target_width):
        d = float(target_width) / self.size[0]
        max_target_width = self.size[0] / 5.0
        return DISTANCE_SCALE * ( max_target_width - target_width ) / max_target_width 


    def filter_targets(self,list_of_contours):
        # given a list of contours, return two lists of PossibleTargets.
        # the first list will have up to two of the best possible targets
        # the other list will have the others that were not selected

        selected = []
        not_selected = []

        possible_targets = [ PossibleTarget(contour,self.center,self.settings) for contour in list_of_contours]

        #sort them by their quality score.
        def sort_by_score(target):
            return target.score()

        sorted_targets = sorted(possible_targets,key=sort_by_score)        
        found = 0
        for target in sorted_targets:
            if found < 2:
                if target.is_acceptable():
                    selected.append(target)
                    found += 1
            else:
                not_selected.append(target)

        return ( selected, not_selected)
    
def diagonal_distance_error( point_list):

    #gives the total square error of 4 points relative to their center
    #a larger number means more likely the contour is not a rectangle
    (x1,y1) = ( point_list[0][0][0], point_list[0][0][1] )
    (x2,y2) = ( point_list[1][0][0], point_list[1][0][1] )
    (x3,y3) = ( point_list[2][0][0], point_list[2][0][1] )
    (x4,y4) = ( point_list[3][0][0], point_list[3][0][1] )

    (cx,cy) = [ (x1 + x2 + x3 + x4) / 4.0 , (y1 + y2 + y3 +y4 ) / 4.0]
    e1 = math.pow( cx-x1, 2) + math.pow(cy-y1, 2)
    e2 = math.pow( cx-x2, 2) + math.pow(cy-y2, 2)
    e3 = math.pow( cx-x3, 2) + math.pow(cy-y3, 2)
    e4 = math.pow( cx-x4, 2) + math.pow(cy-y4, 2)

    return abs(e2 - e1) + abs(e3-e1) + abs(e4-e1) 



class PossibleTarget(object):

    WRONG_VERTICES_WEIGHT = -100001
    CORNER_ERROR_WEIGHT = -100.0
    ASPECT_RATIO_ERROR_WEIGHT = -200.0
    AREA_WEIGHT = 10.0    
    IDEAL_ASPECT_RATIO= 2.5

    MINIMUM_SCORE = -100000
    """
        represents a candidate target in view.
        we assume this is a rectangular target
    """
    def __init__(self, contour,center_reference,settings):

        self.contour = contour
        self.center_reference = center_reference
        self.settings = settings

        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour,self.settings.contour_length * perimeter, True)
        x,y,w,h = cv2.boundingRect(contour)
        approx_points = approx.tolist()

        self.center = (  x + (w / 2.0) ,  y + (h / 2.0 ) )
        
        self.c1 = ( x , y)
        self.c2 = ( x + w, y)
        self.c3 = ( x + w, y + h)
        self.c4 = ( x, y + h )
        self.height = h
        self.width = w
        self.area = w * h

        self.vertices = len(approx)
        self.corner_error = None
        self.aspect_ratio = None
        if self.vertices == 4:
            self.corner_error = diagonal_distance_error(approx_points)
            aspect_ratio = self.height / self.width
            self.aspect_ratio_error = abs(aspect_ratio - PossibleTarget.IDEAL_ASPECT_RATIO)
        else:
            self.corner_error = 0.0

    def is_acceptable(self):
        return self.score() >= PossibleTarget.MINIMUM_SCORE

    def score(self):

        # target quality is higher for better matches.
        # you get huge negative points for n
        score = 0.0
        log.info("Scoring: Vertices=%d" % self.vertices)
        
        if self.vertices != 4:
            score = PossibleTarget.WRONG_VERTICES_WEIGHT
        else:
            score = PossibleTarget.CORNER_ERROR_WEIGHT * self.corner_error
            score += PossibleTarget.ASPECT_RATIO_ERROR_WEIGHT * self.aspect_ratio_error

        log.info ( "Score: %0.2f,  vertices: %d, " % (score, self.vertices) )
        return score
        #score += PossibleTarget.WRONG_VERTICES * abs( self.vertices - 4)
        #score += PossibleTarget.AREA * self.height * self.width
        #score += PossibleTarget.SQUARE_ERROR * self.corner_error()
        #score += PossibleTarget.SYMMETRIC  * self.y_symmetry(self.center_reference[1])


        #return score


