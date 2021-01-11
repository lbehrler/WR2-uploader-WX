# Uploader for SDL Weather Rack 2

> **Note:**: If you have an issue with this project, please review your hardware docuemntation first.  If you are still having an issue or have a software specific issue, please open an issue [here](https://github.com/lbehrler/WR2-uploader-WU/issues).

This is a Raspberry Pi project that retrieves the weather data values (temperature, humidity, wind speed, ..., etc) in JSON format from the Weather Rack 2.  The data is manipulated to meet the [Weather Underground](www.weatherunderground.com); format for uploading of PWS data. I purchased a WeatherRack2 as my first weather station in 2020 and wrote this program to adapt the data feed for my use in both uploading to Weather Underground and in sending basic data to a display (in this case an AstoPi Sense Hat.  There is code included in the distribution to use a Sense Hat or to forgo the display and have a basic data processor and uploader. 

## Required Components

This project is quite easy to make.   

###The Basic [no display] project:
+[Raspberry PI Zero, 3 or 4] (https://www.raspberrypi.org/products/) with appropriate power supply.  During the initial build I constructed the project with a Pi Zero W. I later updated the project to a Pi 4 as a test bed and ulitimately moved the project to a Pi 3B+.
+Raspberry PI case.

###The more advanced project with a Sense Hat display:
+ [Raspberry 3 or 4] (https://www.raspberrypi.org/products/) with appropriate power supply.  During the initial build I constructed the project with a Pi Zero W.   I later updated the project to a Pi 4 as a test bed and ulitimately moved the project to a Pi 3B+.
+ [Astro Pi Sense Hat](https://www.adafruit.com/product/2738).
+ Raspberry PI "hat" case.  There are several cases available for the Pi 3 and 4, make sure if you are using a Sense Hat you purchase a "hat" case to give enough room for the hardware.

## Project Files

The project folder contains several files and one folder:

+ `WUconfig.py` - This is the project's external service configuration file, it provides the weather station with details about your Weather Underground station.
+ `LICENSE` - The license file for this project
+ `readme.md` - This file.
+ `WR2-uploader-WU.py` - A basic data collection application for this project. You'll run this application to collect data from the data stream, process it and upload to Weather Underground.
+ `SH-WR2-uploader-WU.py` - The main data collection application for this project, using both the Weather Rack 2 and the Sense Hat. You'll run this application to collect data from the data stream, display data (inside and outside) on the Sense Hat, and upload to Weather Underground.

## Hardware Assembly

Assembly is easy - mount the Sense HAT on the Raspberry Pi then insert it in the case and plug it into power. All set! No wiring, soldering or anything else required.

> NOTE: The Raspberry Pi foundation recommend you mount the "hat" boards to the Raspberry Pi using [standoffs](http://www.mouser.com/Electromechanical/Hardware/Standoffs-Spacers/_/N-aictf) 

## Weather Underground Setup

Weather Underground (WU) is a public weather service now owned by the Weather Channel; it's most well-known for enabling everyday people to setup weather stations and upload local weather data into the WU weatherbase for public consumption. Point your browser of choice to [https://www.wunderground.com/weatherstation/overview.asp](https://www.wunderground.com/weatherstation/overview.asp) to setup your weather station. Once you complete the setup, WU will generate a station ID and access key you'll need to access the service from the project. Be sure to capture those values, you'll need them later.

## Installation

Download the Raspberry Pi software from [raspberrypi.org](https://www.raspberrypi.org/software/) then burn it to an SD card using the instructions found at [Installing Operating System Images](https://www.raspberrypi.org/documentation/installation/installing-images/README.md). Raspbian should automatically prompt you to select a Wi-Fi network and perform a software update.

When setup completes, you must enable the I2C protocol for the Sense Hat to work correctly. Open the Raspberry menu, select **Preferences**, then **Raspberry Pi Configuration**. When the application opens, select the **Interfaces** tab, enable the I2C protocol and click the **OK** button to save your changes.

![Raspberry Pi Configuration]

Next, open a terminal window and execute the following command:

``` shell
sudo apt install sense-hat
```

This command installs the support packages for the Sense Hat.

Assuming the terminal window is pointing to the Pi user's home folder, in open terminal window, execute the following command:

``` shell
git clone https://github.com/lbehrler/WR2-uploader-WU.git
```

This puts the project files in the current folder's `WR2-uploader-WU` folder.

## Configuration

To upload weather data to the Weather Underground service, the application requires access to the station ID and station access key you created earlier in this setup process. Open the project's `WUconfig.py` in your editor of choice and populate the `STATION_ID` and `STATION_KEY` fields with the appropriate values from your Weather Underground Weather Station:

``` c++
Config:
  # Weather Underground
  STATION_ID = ""
  STATION_KEY = ""
```

Refer to the Weather Underground [Personal Weather Station Network](https://www.wunderground.com/personal-weather-station/mypws) to access these values.


If you’re testing the application and don’t want the weather data uploaded to Weather Underground until you're ready, comment out the "requests.get(" command

## Testing the Application

To execute the data collection application, open a terminal window, navigate to the folder where you copied the project files and execute the following command:

``` shell
sudo python ./SH-WR2-uploader-WU.py
```

### Starting The Project's Application's Automatically


## Revision History

+ 01/06/2021 - initial release

