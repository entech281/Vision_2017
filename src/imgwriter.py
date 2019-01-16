import cv2
import logging
import multiprocessing
from timer import RateTimer
log = logging.getLogger('ImgWriter')

class ImageWriter(multiprocessing.Process):
    
    def __init__(self, task_queue,output_file):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue   
        self.rate_timer = RateTimer("ImageWriter")
        self.output_file = output_file

    def run(self):
        proc_name = self.name
       
        while True:
            next_task = self.task_queue.get()
            if next_task is None:
                # Poison pill means shutdown
                log.warn ('%s: Exiting' % proc_name)
                self.task_queue.task_done()
                
                break
            #print ('%s: Running Job' % (proc_name))            
            cv2.imwrite(self.output_file,next_task)
            self.rate_timer.tick()
            self.task_queue.task_done()
        
        log.warn("Processing finished.")
        return

     