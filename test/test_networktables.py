from networktables import NetworkTables
import time,logging

NetworkTables.enableVerboseLogging()
NetworkTables.setTeam(281)
NetworkTables.setClientMode()
NetworkTables.setUpdateRate(20)
NetworkTables.initialize(server='roborio-281-frc.local')


logging.basicConfig(level=logging.DEBUG, format='[%(name)-10s]: %(asctime)s %(levelname)s %(message)s')
ntlogger = logging.getLogger('nt')
ntlogger.setLevel(logging.DEBUG)

table = NetworkTables.getTable("table")

while True:
    value = table.getString('string','NOVALUE')
    print("Value= '%s' " % value )
    print( table.isConnected() )
    time.sleep(0.5)
    