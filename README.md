# Weatherstation
Setup of my weather station. Here, I try to put all relevant information about my current hobby project of setting up a weatherstation.

## Components
The climate station consists of
1 A sensor module comprissing the following:
1.1 Raspberry Pi Pico running CircuitPython [[Datasheet](https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf)]
1.2 Adafruit AirLift FeatherWing – ESP32 WiFi Co-Processor [[Datasheet](https://www.berrybase.de/en/Pixelpdfdata/Articlepdf/id/7049/onumber/ADA4264)]
1.3 Micro SD Card Reader Module with SPI Interface [[Datasheet](https://www.berrybase.de/en/Pixelpdfdata/Articlepdf/id/5351/onumber/MSD-AADP)]
1.4 MeanWell Series HDR-15 Power Supply (230 V AC to 5 V DC) [[Datasheet](https://www.meanwell.com/Upload/PDF/HDR-15/HDR-15-SPEC.PDF)]
1.5 GIAK DS18B20 Temperature Sensor(s) for measuring soil temperature [[Infosheet](https://m.media-amazon.com/images/I/61JiLatkqdS._SL1080_.jpg)]
1.6 AZDelivery GY-BME280 Barometric Sensor for measuring air temperature, relative humidity and air pressure [[Datasheet](https://m.media-amazon.com/images/I/C1UzCp6wlVS.pdf)]
2 A communication and data distribution unit comprising
2.1 Raspberry Pi 4B 4 GB RAM [[Datasheet](https://www.berrybase.de/en/Pixelpdfdata/Articlepdf/id/5914/onumber/RPI4B-4GB)]
2.2 FritzBox 7170 Router

## Functioning
The idea behind the setup is to measure, store, and visualise environmental parameters. Data are to be collected using the sensors (1.5, 1.6) and the Pi Pico (1.1). Since the Pico W was not available when I got the micro controllers, an additional Adafruit AirLift (1.2) is used to eastablish a wireless connection. A micro SD card is used to prevent data loss, in case a Wifi connection cannot be established.
If the connection between sensor module and router is working, MQTT is used to send strings of sensor data to the MQTT broker running on the Raspberry Pi (2.1).
The Raspberry Pi then saves the data to a USB storage device. Moreover, it can be used to publish the data on a website (local or public).
