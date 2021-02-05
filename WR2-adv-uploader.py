#!/usr/bin/env python3 Weather Underground and PWS Weather Advanced Upload Script for WeatherSense 
# SwitchDoc Labs Weather in combination with the Sense HAT Sensors 
# -------------------------------------------------------------------------------------------------------------------------------------------------------------- 
# Adapted from Switch Doc Labs readWeatherSensors.py script for testing the WeatherRack2 Adapted from 
# John Wargo SH to WU script 
# https://github.com/johnwargo/pi_weather_station/blob/master/weather_station.py 
# --------------------------------------------------------------------------------------------------------------------------------------------------------------
import sys
#import requests
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
from sense_hat import SenseHat

from config import Config

# Python version work around 
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

if (Config.BMP180_ENABLE == True):
    from Adafruit_BMP085 import BMP085
    # Initialise the BMP085 and use STANDARD mode (default value)
    bmp = BMP085(0x77)


# -------------------------------------------------------------------------------------------------------------------------------------------------------------
# Intialize constants

DEBUG_MODE = False
# specifies how often to measure values from the Sense HAT (in minutes)
PWS_INTERVAL = Config.PWS_INTERVAL  # set between 1 and 30 minutes to accomodate PWSweather.com upload requirements
# Set to False when testing the code and/or hardware
# Set to True to enable upload of weather data to Weather Underground
WEATHER_UPLOAD = True

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Initialize global variables
# last_temp = 0
wu_station_id = ''
wu_station_key = ''
pws_station_id = ''
pws_station_key = ''
sense = None
shMsg = ''
base_rain = 0

# to dump rain gauge on a startup mark this as True
dumper = True

# initialize the pass / fail upload counter for services
failct = 0
goodct = 0

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

#  Read Weather Underground Configuration from config file
if (Config.WU_ENABLE == True):
    logging.info('Initializing Weather Underground configuration')
    wu_station_id = Config.WU_STATION_ID
    wu_station_key = Config.WU_STATION_KEY
    if (wu_station_id == "") or (wu_station_key == ""):
        logging.error('Missing values from the Weather Underground configuration file')
        sys.exit(1)
    logging.info('Successfully read WU weather configuration')
    logging.info('WU Station ID: {}'.format(wu_station_id))
    logging.debug('Station key: {}'.format(wu_station_key))

#  Read PWSweather.com Configuration from config file
if (Config.PWS_ENABLE == True):
    logging.info('Initializing PWSweather.com configuration')
    pws_station_id = Config.PWS_STATION_ID
    pws_station_key = Config.PWS_STATION_KEY
    if (pws_station_id == "") or (pws_station_key == ""):
        logging.error('Missing values from the PWS Weather configuration file')
        sys.exit(1)
    logging.info('Successfully read PWSweather configuration')
    logging.info('PWS Station ID: {}'.format(pws_station_id))
    logging.debug('Station key: {}'.format(pws_station_key))

# initialize the date and time 
date_str = "&dateutc=now"  #Default date stamp for weather services

# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Weather station base URL variable initialization

# Weather Underground URL formation 
# Create a string to hold the first part of the URL
# Standard upload
#WUurl = "https://weatherstation.wunderground.com/weatherstation/updateweatherstation.php?"
#WUaction_str = "&action=updateraw"

# Rapid fire server
WUurl = "https://rtupdate.wunderground.com/weatherstation/updateweatherstation.php?"
WUaction_str = "&realtime=1&rtfreq=16"

WUcreds = "ID=" + wu_station_id + "&PASSWORD="+ wu_station_key

# PWS weather URL formation 
# Create a string to hold the first part of the URL
PWSurl = "https://pwsweather.com/weatherstation/updateweatherstation.php?"
PWSaction_str = "&action=updateraw"

PWScreds = "ID=" + pws_station_id + "&PASSWORD="+ pws_station_key

#only run this if there is a Sense HAT
if (Config.SH_ENABLE == True):
    # Set Constants for Sense HAT
    # constants used to display symbols on Sense HAT [up and down arrows plus bars]
    # modified from https://www.raspberrypi.org/learning/getting-started-with-the-sense-hat/worksheet/
    # set up the colours (blue, red, empty)
    b = [0, 0, 255]  # blue
    r = [255, 0, 0]  # red
    g = [0,128,0]    # green
    y = [255,255,0]  # yellow
    e = [0, 0, 0]    # empty

    arrow_up = [
        e, e, e, r, r, e, e, e,
        e, e, r, r, r, r, e, e,
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
    plus = [
        e, e, e, g, g, e, e, e,
        e, e, e, g, g, e, e, e,
        e, e, e, g, g, e, e, e,
        g, g, g, g, g, g, g, g,
        g, g, g, g, g, g, g, g,
        e, e, e, g, g, e, e, e,
        e, e, e, g, g, e, e, e,
        e, e, e, g, g, e, e, e,
    ]

    # Initialize the Sense HAT object
    try:
        logging.info('Initializing the Sense HAT client')
        sense = SenseHat()
        sense.set_rotation(90)
        # then write some text to the Sense HAT
        sense.show_message('Power Up', text_colour=r, back_colour=[0, 0, 0])
        # clear the screen
        sense.clear()
    except:
        logging.info('Unable to initialize the Sense HAT library')
        logging.error('Exception type: {}'.format(type(e)))
        logging.error('Error: {}'.format(sys.exc_info()[0]))
        print (sys.stdout)
        sys.exit(1)

logging.info('Initialization complete!')


# ---------------------------------------------------------------------------------------------------------------------------------------------------------------
# Starting up wireless read from SDR 

# 146 = FT-020T WeatherRack2, #147 = F016TH SDL Temperature/Humidity Sensor
logging.info('Starting Wireless Read')
#cmd = [ '/usr/local/bin/rtl_433', '-vv',  '-q', '-F', 'json', '-R', '146', '-R', '147']
cmd = [ '/usr/local/bin/rtl_433', '-q', '-F', 'json', '-R', '146', '-R', '147']

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

def sh_plus():
    sense.set_pixels(plus)
    time.sleep(1)
    sense.clear()

def sh_arrow():
    sense.set_pixels(arrow_up)
    time.sleep(1)
    sense.clear()

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
    #logging.info('Looking for WR2 data')
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
        if (( sLine.find('F007TH') != -1) or ( sLine.find('F016TH') != -1)):
            logging.info('WeatherSense Indoor T/H F016TH Found')
            logging.info('raw data: ' + sLine)
            # Variable Processing from JSON output from Indoor T/H unit for WU upload
            logging.info('Variable processing of Indoor T/H raw data.')
            raw_data = json.loads(sLine)
            indhumidity_str = "{0:.0f}".format(raw_data['humidity'])
            indtemp_str =  "{0:.1f}".format(raw_data['temperature_F'])
            logging.info('Indoor Temp: ' + indtemp_str)
            logging.info('Indoor Humidity: ' + indhumidity_str)
            if (Config.SH_ENABLE == True):
                # Send the local data to the Sense HAT
                shMsg= indtemp_str + "F " + " " + indhumidity_str + "%"
                sense.show_message(shMsg, text_colour=[255, 255, 0], back_colour=[0, 51, 0])
                # clear the screen
                sense.clear()
        if (( sLine.find('FT0300') != -1) or ( sLine.find('FT020T') != -1)):
            logging.info('WeatherSense WeatherRack2 FT020T found')
            logging.info('raw data: ' + sLine)
            if (Config.SH_ENABLE == True):
                # Variable Processing from SH unit for upload
                logging.info('Variable processing of SH raw data.')
                baro_str = "{0:.2f}".format (sense.get_pressure() * 0.0295300)
            if (Config.BMP180_ENABLE == True):
                # Variable Processing for BMP180 unit for upload
                logging.info('Variable processing of BMP180 raw data.')
                logging.info('Barometer hPa' + str(bmp.readPressure()/100))
                baro_str = "{0:.2f}".format (bmp.readPressure() / 100 * 0.0295300) 
            # Variable Processing from JSON output from WR2 unit for upload
            logging.info('Variable processing of WR2 raw data.')
            raw_data = json.loads(sLine)
            #Convert local time in UTC
            time_str=timeUTC(raw_data['time'])
            # Format process weather variables into strings for  upload
            humidity_str = "{0:.0f}".format(raw_data['humidity'])
            humpct = (raw_data['humidity'])
            tempf = ((raw_data['temperature']-400)/10.0)
            tempc = ((tempf-32.0)*5.0/9.0)
            temp_str =  "{0:.1f}".format((raw_data['temperature']-400.0)/10.0)
            # Dew Point Calcs
            dewptc = get_dew_point_c(tempc, humpct)
            dewpt_str = "{0:.1f}".format((dewptc *9.0/5.0)+32.0)
            winddir_str = "{0:.0f}".format(raw_data['winddirection'])
            avewind_str = "{0:.2f}".format(raw_data['avewindspeed'] * 0.2237)
            gustwind_str = "{0:.2f}".format(raw_data['gustwindspeed'] * 0.2237)
            # Check rain gauge to see if it is the end of the day and time to dump it
            # get the current minute and hour
            current_minute = dt.datetime.now().minute
            current_hour = dt.datetime.now().hour
            logging.info('Current hour: {}'.format(current_hour))
            logging.info('Last hour: {}'.format(last_hour))
            # is it the same day as the last time we checked?
            # this will always be true the first time through this loo
            logging.info('Time for the LAST DAY check')
            if current_hour != last_hour:
                logging.info('Current hour: {}'.format(current_hour))
                logging.info('Last hour: {}'.format(last_hour))
                last_hour = current_hour
                if (dumper == True):
                    logging.info('First run, clearing the rain gauge +++++++++++++++')
                    base_rain = (raw_data['cumulativerain'] * 0.003937)
                    dumper == False
                if ((current_minute == 0) and (current_hour == 0)):
                    # get the reading timestamp
                    now = dt.datetime.now()
                    base_rain = (raw_data['cumulativerain'] * 0.003937)
                    #logging.info("%d day mark (%j @ %s)" % (current_hour, str(now)))
                    logging.info('DUMPING the rain gauge')
                else:
                    logging.info('Not time to dump the rain gauge')
            logging.info('Base rain: {}'.format(base_rain))
            day_rain = ((raw_data['cumulativerain'] * 0.003937) - base_rain)
            dayrain_str = "{0:.2f}".format(day_rain)
            cumrain_str = "{0:.2f}".format(raw_data['cumulativerain'] * 0.003937)
            uv_str = "{0:.1f}".format(raw_data['uv'] * 0.1)
            light_str = "{0:.0f}".format(raw_data['light'])
            if (Config.SH_ENABLE == True):
                # Send the temp / humidity data to the Sense HAT
                shMsg= temp_str +  "F " + " " + humidity_str + "%"
                sense.show_message(shMsg, text_colour=[255, 255, 0], back_colour=[0, 0, 102])
                # clear the screen
                sense.clear()
            #build weather packet for sending
            weather_data = {
                'dateutc': time_str,
               #'dateutc':"now",
                'tempf': temp_str,
                'humidity': humidity_str,
                'dewptf': dewpt_str,
                'winddir': winddir_str,
                'windspeedmph': avewind_str,
                'windgustmph': gustwind_str,
                'dailyrainin': dayrain_str,
                'uv': uv_str,
                'baromin': baro_str,
                'softwaretype':str("WR2-Advanced-Updater"),
                    }
            # Form URL into WU format and Send
            if (Config.WU_ENABLE == True):
                # From http://wiki.wunderground.com/index.php/PWS_-_Upload_Protocol
                logging.info('--------------Uploading data to Weather Underground')
                try:
                    upload_url = WUurl + WUcreds +"&" + urlencode(weather_data) + WUaction_str
                    #logging.info('Raw URL',upload_url)
                    response = urllib.request.urlopen(upload_url)
                    html = response.getcode()
                    logging.info('Server response: {}'.format(html))
                    # best practice to close the file
                    response.close()
                except:
                    logging.info('Excepting Weather Underground upload')
                    #logging.error('Exception type: {}'.format(type(e)))
                    logging.error('Error: {}'.format(sys.exc_info()[0]))
                    #traceback.print_exc(file=sys.stdout)
            else:
                logging.info('Elsing Skipping Weather Underground upload')
            # PWS weather upload
            # Check upload time against interval to insure weather data is sent to PWSweather.com once every 1-30 minutes
            # get the current minute
            current_minute = dt.datetime.now().minute
            logging.info('Current minute: {}'.format(current_minute))
            # is it the same minute as the last time we checked?
            # this will always be true the first time through this loop
            if current_minute != last_minute:
                # reset last_minute to the current_minute
                last_minute = current_minute
                # is minute zero, or divisible by 10?
                # we're only going to use measurements every PWS_INTERVAL minutes
                if (Config.PWS_ENABLE == True and ((current_minute == 0) or ((current_minute % PWS_INTERVAL) == 0))):
                    # get the reading timestamp
                    now = dt.datetime.now()
                    logging.info("%d minute mark (%d @ %s)" % (PWS_INTERVAL, current_minute, str(now)))
                    # Form URL into PWS format and Send
                    logging.info('++++++++++++++++++Uploading data to PWS weather')
                    try:
                        upload_url = PWSurl + PWScreds +"&" + urlencode(weather_data) + PWSaction_str
                        #logging.info('Raw URL ' + upload_url)
                        response = urllib.request.urlopen(upload_url)
                        html = response.getcode()
                        logging.info('Server response: {}'.format(html))
                        # best practice to close the file
                        response.close()
                    except:
                        logging.info('Excepting PWS Weather upload')
                        #logging.error('Exception type: {}'.format(type(e)))
                        logging.error('Error: {}'.format(sys.exc_info()[0]))
                        #traceback.print_exc(file=sys.stdout)
                else:
                    logging.info('Skipping PWSweather.com upload')

                # Show a copy of what you formed up and are uploading in HRF
                logging.info('Time Stamp ' + time_str)
                logging.info('Outdoor Temp ' + temp_str)
                logging.info('Humidity ' + humidity_str)
                logging.info('Dew Point ' + dewpt_str)
                logging.info('Wind Direction ' + winddir_str)
                logging.info('Wind Speed Ave ' + avewind_str)
                logging.info('Wind Speed Gust ' + gustwind_str)
                logging.info('Rain total ' + cumrain_str)
                logging.info('UV ' + uv_str)
                logging.info('Light ' + light_str)
                logging.info('Barometer ' + baro_str)
                logging.info('Software WR2-Advanced-Updater')
            """
            # Check WU Feed Status
            logging.info('WU Received ' + str(wur.status_code) + ' ' + str(wur.text))
            # display  green cross for success or a red arrow for fail
            if (wur.status_code == 200):
                if (Config.SH_ENABLE == True):
                    sh_plus()
                # increase good upload count
                goodct += 1
                logging.info('Good Upload Count: {}'.format(goodct) + ' Failed Upload Count: {}'.format(failct))
            else:
                if (Config.SH_ENABLE == True):
                    sh_arrow()
                # increase fail upload count 
                failct += 1
                logging.info('Good Upload Count: {}'.format(goodct) + ' Failed Upload Count: {}'.format(failct))
            """
        sys.stdout.flush()
