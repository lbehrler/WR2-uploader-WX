#!/usr/bin/env python3 Air Qaulity Open Data Platform Upload Script for Air Quality Monitor
# SwitchDoc Labs AQI Solar
# -------------------------------------------------------------------------------------------------------------------------------------------------------------- 
# Adapted from Switch Doc Labs readWeatherSensors.py script for testing the WeatherRack2 Adapted from 
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
import sys
import requests
from subprocess import PIPE, Popen, STDOUT
from threading  import Thread
import json
import datetime as dt
from datetime import datetime
#import pytz
from pytz import timezone
#import time
import logging
import traceback
import math
import urllib
import urllib.request

from config import Config

# Python version work around 
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode
    
# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# Intialize constants

DEBUG_MODE = False
# Set to False when testing the code and/or hardware
# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Initialize global variables
# last_temp = 0

# Setup the basic console logger
format_str = '%(asctime)s %(levelname)s %(message)s'
date_format = '%Y-%m-%d %H:%M:%S'
logging.basicConfig(format=format_str, level=logging.INFO, datefmt=date_format)
# When debugging, uncomment the following two lines
# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)

# initialize the lastMinute variable to the current time to start
last_minute = dt.datetime.now().minute
last_hour = dt.datetime.now().hour

# on init, just use the previous minute as lastMinute
last_minute -= 1
if last_minute == 0:
    last_minute = 59
    logging.debug('Last Minute: {}'.format(last_minute))

# on init, use previos day as last_day
last_hour -= 1
logging.info('Last Hour: {}'.format(last_hour))

# ------------------------------------------------------------------------------------------------------------------------------------------------------------
# URL Formation and WU/PWS initialization
logging.info('Starting Init')

#  Read AQODP Configuration from config file
if (Config.AQ_ENABLE == True):
    logging.info('Initializing AQ ODP configuration')
    if (Config.AQ_STATION_ID == "") or (Config.AQ_STATION_NAME == ""):
        logging.error('Missing values from the Weather Underground configuration file')
        sys.exit(1)
    logging.info('Successfully read AQ ODP configuration')
    logging.info('AQ Station ID: {}'.format(Config.AQ_STATION_ID))
    logging.debug('Station key: {}'.format(Config.AQ_STATION_NAME))
    AQstation = {'id':Config.AQ_STATION_ID, 'name':Config.AQ_STATION_NAME, 'location':Config.LOCATION} 
    AQurl = "https://aqicn.org/sensor/upload/"

# initialize the date and time 
date_str = "&dateutc=now"  #Default date stamp for weather services

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# AQODP station base URL variable initialization

# Weather Underground URL formation 
# Create a string to hold the first part of the URL
# Standard upload

logging.info('Initialization complete!')

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Starting up wireless read from SDR 

# 146 = FT-020T WeatherRack2, #147 = F016TH SDL Temperature/Humidity Sensor
logging.info('Starting Wireless Read')
#cmd = [ '/usr/local/bin/rtl_433', '-vv',  '-q', '-F', 'json', '-R', '146', '-R', '147']
cmd = [ '/usr/local/bin/rtl_433', '-q', '-F', 'json', '-R', '148', '-R', '150']

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
#   Functions 

def nowStr():
    return( datetime.datetime.now().strftime( '%Y-%m-%d %H:%M:%S'))

def timeUTC(time_stamp):
    # Convert Timestamp from local Timezone to UTC using timestamp from WR2
    # Adjust values below to match your timezone etc
    utc = timezone('UTC')
    central = timezone('US/Central')
    published_time = datetime.strptime(time_stamp, '%Y-%m-%d %H:%M:%S')
    published_cst = published_time.replace(tzinfo=central)
    published_gmt = published_time.astimezone(utc)
    actual_time_published = published_gmt.strftime('%Y-%m-%d %H:%M:%S')
    # URL Encode timestamp and return
    #url_str = urllib.parse.quote_plus(actual_time_published,encoding=None, errors=None)
    return (actual_time_published)

#   We're using a queue to capture output as it occurs
try:
    from Queue import Queue, Empty
except ImportError:
    from queue import Queue, Empty  # python 3.x
ON_POSIX = 'posix' in sys.builtin_module_names

def enqueue_output(src, out, queue):
    for line in iter(out.readline, b''):
        queue.put(( src, line))
        logging.debug('Queue Size {}'.format(queue.qsize()))
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
logging.info('Looking for AQI data')
while True:
    #   Other processing can occur here as needed...
    try:
        src, line = q.get(timeout = 1)
        #print(line.decode())
    except Empty:
        pulse += 1
    else: # got line
        pulse -= 1
        sLine = line.decode()
        #print(sLine)
        #   See if the data is something we need to act on...
        if ( sLine.find('AQI') != -1):
            logging.info('WeatherSense AQI found')
            logging.info('raw data: ' + sLine) 
            # Variable Processing from JSON output from AQI unit for upload
            logging.info('Variable processing of AQI raw data.')
            raw_data = json.loads(sLine)
            #Convert local time in UTC
            time_str=timeUTC(raw_data['time'])
            # Format process weather variables into strings for  upload

            PM1S_str = "{0:.0f}".format(raw_data['PM1.0S'])
            PM25S_str =  "{0:.0f}".format(raw_data['PM2.5S'])
            PM10S_str = "{0:.0f}".format(raw_data['PM10S'])
            AQI_str = "{0:.0f}".format(raw_data['AQI'])
           
            # JSONify data
            sensorReadings = [
                {'specie':'pm2.5', 'value':raw_data['PM2.5S']},
                {'specie':'pm10', 'value':raw_data['PM10S']},
                {'specie':'pm1.0', 'value':raw_data['PM1.0S']},
                {'specie':'aqi', 'value':raw_data['AQI']}
            ]
                    
            # build packet for sending
            aq_data = {'station': AQstation, 'readings':sensorReadings,'token': Config.TOKEN}
            # Form URL into WU format and Send
            if (Config.AQ_ENABLE == True):
                logging.info('--------------Uploading data to AQI ODP')
                request = requests.post (AQurl, json = aq_data)
                print(request.text)
                data = request.json()
                if data["status"]!="ok": 
                    print("Something went wrong: %s" % data) 
                else: 
                    print("Data successfully posted: %s"%data) 
            else:
                logging.info('Elsing Skipping AQI upload')

        sys.stdout.flush()
