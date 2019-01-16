#!/bin/sh
#
# starts mjpg_streamer
# this is a file for two reason
# (1) we need to do a one-time check to set up the camera file
# (2) mjpg_streamer forks itself in a strange way, so that supervisor does not get the right pid
CAMERA_FILE="/run/camera"
PORT=5801

echo "Starting Camera..."
# create camera if necessary
if [ ! -d "$CAMERA_FILE" ]; then
   sudo mkdir $CAMERA_FILE
   sudo chown -R pi:pi $CAMERA_FILE
fi

#kill old streamers if necessary

PIDS=$(ps -e | grep streamer | awk '{ print $1;}')
if [ -z $PIDS ]; then
   echo "No Old Processes to Kill"
else
   echo "killing old process $PIDS"
   kill -9 $PIDS
fi

#run mjpg streamer
MSTREAM_HOME=/opt/mjpg-streamer/mjpg-streamer
export LD_LIBRARY_PATH=$MSTREAM_HOME
$MSTREAM_HOME/mjpg_streamer -i "$MSTREAM_HOME/input_file.so -f $CAMERA_FILE -n vision.jpg" -o "$MSTREAM_HOME/output_http.so -w $MSTREAM_HOME/www -p $PORT" 
