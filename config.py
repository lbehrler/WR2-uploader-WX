class Config:
  # Weather Underground
  WU_ENABLE = True
  WU_STATION_ID = "KTXMANSF125"
  WU_STATION_KEY = "VpAEW0HV"

  # PWSweather.com
  PWS_ENABLE = True
  PWS_STATION_ID = "KTXMANSF125"
  PWS_STATION_KEY = "SEF.treh7neng*bran"
  PWS_INTERVAL = 2   # Number of minutes (1-30)
  
  # Windy.com
  WDY_ENABLE = True
  WDY_STATION_ID = 0
  WDY_STATION_NAME = "KTXMANSF125"
  WDY_STATION_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjaSI6MjI0MjU5LCJpYXQiOjE2MjA0OTUzNTN9.KbtXRnqzrMv8G9s9-LO3P6mWLabFQGfHEwGCd9vehFI"
  WDY_INTERVAL = 6   # Number of minutes (1-30)
  
  # AQIcn.org
  AQ_ENABLE = True
  AQ_STATION_ID = "MANS-TX-USA-01"
  AQ_STATION_NAME = "KMANSTX125"
  LOCATION = {'latitude': 32.6011, 'longitude': -97.09922}
  TOKEN    = "98743a8f2bad2dc7bfbf6f43bbd9cab9d2d675ab"
 
  # Sense Hat
  SH_ENABLE = False
  
  # Barometer settings
  baro = True
  
  # BMP280
  BMP280_ENABLE = True

  # BMP180  - Depreciated
  BMP180_ENABLE = False