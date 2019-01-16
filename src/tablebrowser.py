from networktables import NetworkTables
import time

NetworkTables.enableVerboseLogging()
NetworkTables.setTeam(NetworkTablesPositionReporter.TEAM_281)
NetworkTables.setClientMode()
NetworkTables.setUpdateRate(NetworkTablesPositionReporter.UPDATE_RATE_MS)


table = NetworkTables.getTable(NetworkTablesPositionReporter.POSITION_TABLE)

while True:
  pos = table.getBoolean(
