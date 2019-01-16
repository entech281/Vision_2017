from networktables import NetworkTables
from timer import RateTimer
import logging
from data import Constants

log = logging.getLogger("Reporter")

class TestTargetPositionReporter(object):

    def report_position(self,control_position):
        pass
        #print (str(control_position))
    
    def shutdown(self):
        pass

def setNetworkTablesLogging(debug_mode):
    ntlogger = logging.getLogger('nt')
    if debug_mode:
        ntlogger.setLevel(logging.INFO)
    else:
        ntlogger.setLevel(logging.INFO)

class NetworkTablesPositionReporter(object):

    def __init__(self):
        self.timer = RateTimer("NetworkTableReporter",200)
        self.sequence= 0
        NetworkTables.enableVerboseLogging()
        NetworkTables.setTeam(Constants.TEAM_281)
        NetworkTables.setClientMode()
        NetworkTables.setUpdateRate(Constants.UPDATE_RATE_MS)
        NetworkTables.initialize(server=Constants.RIO_HOST)
        self.position_table = NetworkTables.getTable(Constants.POSITION_TABLE)
        log.info("started")

    def report_position(self, control_position):
        self.sequence += 1
        t = self.position_table
        t.putBoolean(Constants.FOUND_KEY,control_position.found)
        t.putNumber(Constants.PI_SEQUENCE,self.sequence)
        t.putNumber(Constants.DIRECTION_KEY,control_position.direction)
        t.putNumber(Constants.DISTANCE_KEY,control_position.distance)
        t.putNumber(Constants.NUM_TARGETS_KEY,control_position.num_targets)
        self.timer.tick()
       
        if self.sequence % 200 == 0:
           setNetworkTablesLogging( self.position_table.isConnected() )
               
           rio_alive = self.position_table.getBoolean(Constants.RIO_ALIVE,False)
           log.info("Rio Alive=" + str(rio_alive))
        
    def shutdown(self):
        NetworkTables.shutdown()
        log.info("shutdown complete.")
