# Weather Underground Upload Script for WeatherSense SwitchDoc Labs Weather Sensors
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Adapted from Switch Doc Labs readWeatherSensors.py script for testing the WeatherRack2
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
import sys
import requests
from subprocess import PIPE, Popen, STDOUT
from threading  import Thread
import json
import datetime
import time
from wuconfig import Config
import math

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------------------------------------------------------------------------------------------

# specifies how often to measure values from Weather Rack (in seconds)
MEASUREMENT_INTERVAL = 60  # in seconds
# Set to False when testing the code and/or hardware
# Set to True to enable upload of weather data to Weather Underground
WEATHER_UPLOAD = True
# some string constants
wu_station_id = ''
wu_station_key = ''


# -------------------------------------------------------------------------------------------------------------------------------------------------------------$
# URL Formation and WU initialization

# ============================================================================
#  Read Weather Underground Configuration
# ============================================================================
('Initializing Weather Underground configuration')
wu_station_id = Config.STATION_ID
wu_station_key = Config.STATION_KEY
if (wu_station_id == "") or (wu_station_key == ""):
    sys.stdout.write('Missing values from the Weather Underground configuration file')
    sys.exit(1)

# we made it this far, so it must have worked...
sys.stdout.write('Successfully read Weather Underground configuration')
sys.stdout.write('Station ID: {}'.format(wu_station_id))

# create a string to hold the first part of the URL
# used for standard upload
WUurl = "https://weatherstation.wunderground.com/weatherstation\
/updateweatherstation.php?"

# rapid fire server
#WUurl = "https://rtupdate.wunderground.com/weatherstation\
#/updateweatherstation.php?"

WUcreds = "ID=" + wu_station_id + "&PASSWORD="+ wu_station_key
date_str = "&dateutc=now"

action_str = "&action=updateraw"
#action_str = "&realtime=1&rtfreq=15"

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# 146 = FT-020T WeatherRack2, #147 = F016TH SDL Temperature/Humidity Sensor
print("Starting Wireless Read")
#cmd = [ '/usr/local/bin/rtl_433', '-vv',  '-q', '-F', 'json', '-R', '146', '-R', '147']
cmd = [ '/usr/local/bin/rtl_433', '-q', '-F', 'json', '-R', '146', '-R', '147']

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#   A few helper functions...

def nowStr():
    return( datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S'))

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#stripped = lambda s: "".join(i for i in s if 31 < ord(i) < 127)


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

def get_dew_point_c(t_air_c, rel_humidity):
    """Compute the dew point in degrees Celsius

    :param t_air_c: current ambient temperature in degrees Celsius
    :type t_air_c: float
    :param rel_humidity: relative humidity in %
    :type rel_humidity: float
    :return: the dew point in degrees Celsius
    :rtype: float
    """
    A = 17.27
    B = 237.7
    alpha = ((A * t_air_c) / (B + t_air_c)) + math.log(rel_humidity/100.0)
    return (B * alpha) / (A - alpha)

#   Create our sub-process...
#   Note that we need to either ignore output from STDERR or merge it with STDOUT due to a limitation/bug somewhere under the covers of "subprocess"
#   > this took awhile to figure out a reliable approach for handling it...
p = Popen(cmd, stdout=PIPE, stderr=STDOUT, bufsize=1, close_fds=ON_POSIX)
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
            #r= requests.get(
            #    WUurl +
            #    WUcreds +
            #    date_str +
            #    "&indoortempf=" + indtemp_str +
            #    "&indoorhumidity=" + indhumidity_str +
            #    "&softwaretype=" + "RaspberryPi" +
            #    action_str)
            # Show a copy of what you formed up and are uploading in HRF 
            print (WUurl +
                WUcreds +
                date_str +
                "&indoortempf=" + indtemp_str +
                "&indoorhumidity=" + indhumidity_str +
                "&softwaretype=" + "RaspberryPi" +
                action_str)
            # Check WU Feed Status
            # print("Received " + str(r.status_code) + " " + str(r.text))

        if (( sLine.find('FT0300') != -1) or ( sLine.find('FT020T') != -1)):
            sys.stdout.write('WeatherSense WeatherRack2 FT020T found' + '\n')
            sys.stdout.write('This is the raw data: ' + sLine + '\n')
            # Variable Processing from JSON output from WR2 unit for WU upload
            sys.stdout.write('Variable processing of WR2 raw data. \n')
            raw_data = json.loads(sLine)
            humidity_str = "{0:.0f}".format(raw_data['humidity'])
            humpct = (raw_data['humidity'])
            tempf = ((raw_data['temperature']-400)/10.0)
            tempc = ((tempf-32.0)*5.0/9.0)
            temp_str =  "{0:.1f}".format((raw_data['temperature']-400.0)/10.0)
            # Dew Point Calcs
            # dewptc  = ((tempc)-((100-raw_data['humidity'])/5))
            dewptc = get_dew_point_c(tempc, humpct)
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
                "&softwaretype=" + "R-Pi-0W" +
                action_str)
            # Show a copy of what you formed up and are uploading in HRF 
            sys.stdout.write(WUurl +
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
                "&softwaretype=" + "R-Pi-0W" +
                action_str)

            # Check WU Feed Status
            print("Received " + str(r.status_code) + " " + str(r.text))
            time.sleep(MEASUREMENT_INTERVAL)

    sys.stdout.flush()
