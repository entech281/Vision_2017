
import time
import logging

log = logging.getLogger("Timer")
class Timer(object):
    """
        Tracks timings of loops. 
        Currently only tracks the most recent, vs averages, which would be a future feature
    """
    def __init__(self,autoReportInterval=100):
        
        self.autoReportInterval = autoReportInterval
        self.loopCount = 0
        self.loopTime = 1.0
        self.running = {}
        self.timings = {}

    def start(self, timer_name):
        self.running[timer_name] = time.time()

    def end(self, timer_name):
        start_time = self.running.get(timer_name)
        if start_time:
            self.timings[timer_name] = time.time() - start_time
        else:
            raise ValueError("Timer " + timer_name + " is still running")

    def get_time(self,timer_name):
        return self.timings.get(timer_name)

    def start_loop(self):
        self.start("loop")
    
    def loop_time(self):
        return self.get_time("loop")

    def end_loop(self):
        self.end("loop")
        self.loopCount = self.loopCount + 1
        if (self.loopCount % self.autoReportInterval == 0) and self.autoReportInterval > 0 :
           print ( str(self) )

    def get_fps(self):
        loop_time = self.loop_time()
        if loop_time and loop_time > 0:
            return 1.0 / loop_time
        else:
            return 0.0

    def __str__(self):
        d = {
           'timings': dict(self.timings),
           'fps' : self.get_fps()
        }
        return str(d)

class FpsTimer(object):
    def __init__(self,fps=10.0):
        self.last=time.time()
        self.ticks = 1.0/fps #seconds between frames

    def should_tick(self):
        now = time.time()
        if now > self.ticks + self.last:
            self.last = now
            return True
        return False         

class RateTimer(object):
    def __init__(self,name,report_interval=100):
        self.count = 0
        self.start = time.time()
        self.report_interval = report_interval
        self.name = name

    def tick(self):
        self.count += 1
        if self.count % self.report_interval == 0:
            log.info("%s Rate: %0.2f" % (self.name, self.get_rate()) )
    def get_rate(self):
        end = time.time()
        return self.count / ( end - self.start )
        self.start = time.time()   


def test_timer():
    t = Timer(autoReportInterval=2)
    for i in range(10):
        t.start_loop()
        time.sleep(0.2)
        t.start("0.1 sec")
        time.sleep(0.1)
        t.end("0.1 sec")
        t.end_loop()

    print (str(t))
    assert t.get_fps() > 0 
    assert t.get_time("0.1 sec") < 0.11 and t.get_time("0.1 sec") > 0.1
    assert t.loop_time() < 0.31 and t.loop_time() > 0.3

if __name__ == '__main__':
    test_timer()