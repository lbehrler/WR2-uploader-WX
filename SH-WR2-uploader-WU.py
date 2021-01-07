# Weather Underground Upload Script for WeatherSense SwitchDoc Labs Weather in combination with the SenseHat Sensors
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
# Adapted from Switch Doc Labs readWeatherSensors.py script for testing the WeatherRack2
# Adapted from John Wargo SH to WU script https://github.com/johnwargo/pi_weather_station/blob/master/weather_station.py
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
import sys
import requests
from subprocess import PIPE, Popen, STDOUT
from threading  import Thread
import json
import datetime
import time
import logging

from sense_hat import SenseHat

from wuconfig import Config

# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------------------------------------------------------------------------------------------

DEBUG_MODE = True
# specifies how often to measure values from the Sense HAT (in minutes)
MEASUREMENT_INTERVAL = 1  # minutes
# Set to False when testing the code and/or hardware
# Set to True to enable upload of weather data to Weather Underground
WEATHER_UPLOAD = True
# some string constants
# SINGLE_HASH = '#'
# HASHES = '############################################'

# constants used to display an up and down arrows plus bars
# modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
# set up the colours (blue, red, empty)
b = [0, 0, 255]  # blue
r = [255, 0, 0]  # red
e = [0, 0, 0]  # empty
# create images for up and down arrows
arrow_up = [
    e, e, e, r, r, e, e, e,
    e, e, r, r, r, r, e, e,
    e, r, e, r, r, e, r, e,
    r, e, e, r, r, e, e, r,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e,
    e, e, e, r, r, e, e, e
]
arrow_down = [
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    e, e, e, b, b, e, e, e,
    b, e, e, b, b, e, e, b,
    e, b, e, b, b, e, b, e,
    e, e, b, b, b, b, e, e,
    e, e, e, b, b, e, e, e
]
bars = [
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e,
    r, r, r, r, r, r, r, r,
    r, r, r, r, r, r, r, r,
    b, b, b, b, b, b, b, b,
    b, b, b, b, b, b, b, b,
    e, e, e, e, e, e, e, e,
    e, e, e, e, e, e, e, e
]

# Initialize some global variables
# last_temp = 0
wu_station_id = ''
wu_station_key = ''
sense = None



# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# URL Formation and WU initialization 
# -------------------------------------------------------------------------------------------------------------------------------------------------------------

#  Read Weather Underground Configuration
logging.info('Initializing Weather Underground configuration')
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
if (wu_station_id is None) or (wu_station_key is None):
    logging.warning('Missing values from the Weather Underground configuration file')
    sys.exit(1)

# we made it this far, so it must have worked...
logging.info('Successfully read Weather Underground configuration')
logging.info('Station ID: {}'.format(wu_station_id))
logging.debug('Station key: {}'.format(wu_station_key))

# Create a string to hold the first part of the URL
# Standard upload
#WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
#action_str = "&action=updateraw"

# Rapid fire server
WUurl = "https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php?"
action_str = "&realtime=1&rtfreq=15"

#wu_station_id = "XXXX" # Replace XXXX with your PWS ID
#wu_station_key = "YYYY" # Replace YYYY with your Password
WUcreds = "ID=" + wu_station_id + "&PASSWORD="+ wu_station_key
date_str = "&dateutc=now"

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# 146 = FT-020T WeatherRack2, #147 = F016TH SDL Temperature/Humidity Sensor
logging.info('Starting Wireless Read')
#cmd = [ '/usr/local/bin/rtl_433', '-vv',  '-q', '-F', 'json', '-R', '146', '-R', '147']
cmd = [ '/usr/local/bin/rtl_433', '-q', '-F', 'json', '-R', '146', '-R', '147']

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#   A few helper functions...

def nowStr():
    return( datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S'))

#   We're using a queue to capture output as it occurs
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x
ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(src, out, queue):
    for line in iter(out.readline, b''):
        queue.put(( src, line))
    out.close()

#   Create our sub-process...
#   Note that we need to either ignore output from STDERR or merge it with STDOUT due to a limitation/bug somewhere under the covers of "subprocess"
#   > this took awhile to figure out a reliable approach for handling it...
p = Popen( cmd, stdout=PIPE, stderr=STDOUT, bufsize=1, close_fds=ON_POSIX)
q = Queue()

t = Thread(target=enqueue_output, args=('stdout', p.stdout, q))

t.daemon = True # thread dies with the program
t.start()

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------

pulse = 0
while True:
   #   Other processing can occur here as needed...
   #sys.stdout.write('Made it to processing step. \n')
   
   try:
      src, line = q.get(timeout = 1)
      #print(line.decode())
    except Empty:
        pulse += 1
    else: # got line
        pulse -= 1
        sLine = line.decode()
        print(sLine)
        #   See if the data is something we need to act on...
        if (( sLine.find('F007TH') != -1) or ( sLine.find('F016TH') != -1)):
            sys.stdout.write('WeatherSense Indoor T/H F016TH Found' + '\n')
            sys.stdout.write('This is the raw data: ' + sLine + '\n')

            # Variable Processing from JSON output from Indoor T/H unit for WU upload
            sys.stdout.write('Variable processing of Indoor T/H raw data. \n')
            raw_data = json.loads(sLine)
            indhumidity_str = "{0:.0f}".format(raw_data['humidity'])
            indtemp_str =  "{0:.1f}".format(raw_data['temperature_F'])

            # Form URL into WU format and Send
            r= requests.get(
                WUurl +
                WUcreds +
                date_str +
                "&indoortempf=" + indtemp_str +
                "&indoorhumidity=" + indhumidity_str +
                "&softwaretype=" + "RaspberryPi" +
                action_str)
            # Show a copy of what you formed up and are uploading in HRF 
            print (WUurl +
                WUcreds +
                date_str +
                "&indoortempf=" + indtemp_str +
                "&indoorhumidity=" + indhumidity_str +
                "&softwaretype=" + "RaspberryPi" +
                action_str)
            # Check WU Feed Status
            print("Received " + str(r.status_code) + " " + str(r.text))

        if (( sLine.find('FT0300') != -1) or ( sLine.find('FT020T') != -1)):
            sys.stdout.write('WeatherSense WeatherRack2 FT020T found' + '\n')
            sys.stdout.write('This is the raw data: ' + sLine + '\n')

            # Variable Processing from JSON output from WR2 unit for WU upload
            sys.stdout.write('Variable processing of WR2 raw data. \n')
            raw_data = json.loads(sLine)
            humidity_str = "{0:.0f}".format(raw_data['humidity'])
            tempf = ((raw_data['temperature']-400)/10.0)
            tempc = ((tempf-32.0)*5.0/9.0)
            temp_str =  "{0:.1f}".format((raw_data['temperature']-400.0)/10.0)
            dewptc  = ((tempc)-((100-raw_data['humidity'])/5))
            dewpt_str = "{0:.1f}".format((dewptc *9.0/5.0)+32.0)
            winddir_str = "{0:.0f}".format(raw_data['winddirection'])
            avewind_str = "{0:.2f}".format(raw_data['avewindspeed'] * 0.2237)
            gustwind_str = "{0:.2f}".format(raw_data['gustwindspeed'] * 0.2237)
            cumrain_str = "{0:.2f}".format(raw_data['cumulativerain'] * 0.003937)
            uv_str = "{0:.1f}".format(raw_data['uv'] * 0.1)
            light_str = "{0:.0f}".format(raw_data['light'])
            # Form URL into WU format and Send
            r= requests.get(
                WUurl +
                WUcreds +
                date_str +
                "&tempf=" + temp_str +
                "&humidity=" + humidity_str +
                "&dewptf=" + dewpt_str +
                "&winddir=" + winddir_str  +
                "&windspeedmph=" + avewind_str +
                "&windgustmph=" + gustwind_str +
                "&dailyrainin=" + cumrain_str +
                "&uv=" + uv_str +
                "&softwaretype=" + "RaspberryPi" +
                action_str)
            # Show a copy of what you formed up and are uploading in HRF 
            print (WUurl +
                WUcreds +
                date_str +
                "&tempf=" + temp_str +
                "&humidity=" + humidity_str +
                "&dewptf=" + dewpt_str +
                "&winddir=" + winddir_str  +
                "&windspeedmph" + avewind_str +
                "&windgustmph=" + gustwind_str +
                "&dailyrainin=" + cumrain_str +
                "&uv=" + uv_str +
                "&softwaretype=" + "RaspberryPi" +
                action_str)
            # Check WU Feed Status
            print("Received " + str(r.status_code) + " " + str(r.text))
            #time.sleep(90)

    sys.stdout.flush()
