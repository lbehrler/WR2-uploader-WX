class Config:
  # Weather Underground
  WU_ENABLE = True
  WU_STATION_ID = ""
  WU_STATION_KEY = ""

  # PWSweather.com
  PWS_ENABLE = True
  PWS_STATION_ID = ""
  PWS_STATION_KEY = ""
  PWS_INTERVAL = 2   # Number of minutes (1-30)
  
  # Windy.com
  WDY_ENABLE = True
  WDY_STATION_ID = 0
  WDY_STATION_NAME = ""
  WDY_STATION_KEY = ""
  WDY_INTERVAL = 2   # Number of minutes (1-30)
  
  # AQIcn.org
  AQ_ENABLE = True
  AQ_STATION_ID = ""
  AQ_STATION_NAME = ""
  LOCATION = {'latitude': 0000000, 'longitude': 0000000}
  TOKEN    = ""
 
  # Sense Hat
  SH_ENABLE = False
  
  # Barometer settings
  baro = True
  
  # BMP280
  BMP280_ENABLE = True
