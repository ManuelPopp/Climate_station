######################################################
### Configuration
######################################################
import board
import busio
import sdcardio
import storage
from digitalio import DigitalInOut
import adafruit_requests as requests
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi
from adafruit_bme280 import basic as af_bme280
from adafruit_onewire.bus import OneWireBus
import adafruit_ds18x20
from time import sleep, localtime, mktime
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_requests import get

## Wifi setup
# Get wifi login info
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
# select Wifi credentials from dictionary with multiple entries
d = 0
ssid, pw = secrets[f"ssid%d" %d], secrets["password%d" %d]

# Raspberry Pi RP2040 Pinout for Wifi
esp32_cs = DigitalInOut(board.GP13)
esp32_ready = DigitalInOut(board.GP14)
esp32_reset = DigitalInOut(board.GP15)

spi_1 = busio.SPI(board.GP10, board.GP11, board.GP12)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi_1, esp32_cs, esp32_ready, esp32_reset)

requests.set_socket(socket, esp)

# Check status
if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 found and in idle mode")
print("Firmware vers.", esp.firmware_version)
print("MAC addr:", [hex(i) for i in esp.MAC_address])

#-----------------------------------------------------
## DS18B20 setup
ow_bus = OneWireBus(board.GP16)
ow_devices = ow_bus.scan()

#-----------------------------------------------------
## BME280 setup
i2c_0 = busio.I2C(sda = board.GP0, scl = board.GP1)

#-----------------------------------------------------
## Format values for export
exportformat = "{t0}"
for device in ow_devices:
    exportformat += ("&" + "{ds18b20_" + str(device.crc) + "}")

exportformat += "&{bme280_0}"
export_list = ["Time"]
exportformat = "{}"
for device in ow_devices:
    exportformat += "&{}"
    export_list.append("ds18b20_" + str(device.crc))

exportformat += "&{}&{}&{}"
export_list.append("bme280_0:T")
export_list.append("bme280_0:p")
export_list.append("bme280_0:rH")

#-----------------------------------------------------
## Callback methods
def connected(client, data, flags, rc):
    print("Connected to client.")

def disconnected(client):
    print("Disconnected from client.")

def get_broker_ip():
    '''
    try:
        response = get("https://www.dropbox.com/s/4zk2jt5iggbcc2d/my_location.txt?raw=1")
        content = response.text
        response.close()
        return content
    except:
        print("Failed fetching broker id.")
    '''
    return "192.168.178.27"

#-----------------------------------------------------
## Time intervals
interval = 60 * 10

def sleep_interval(t_0, seconds = interval):
    t_0_int = mktime(t_0)
    t_now_int = mktime(localtime())
    t_1_int = t_0_int + seconds
    t_delta = (t_1_int - t_now_int)
    if t_delta > 0:
        sleep(t_delta)
    else:
        print("Processing time exceeded measuring interval! Proceeding without sleep.")

#-----------------------------------------------------
## SD-card setup
# SD MISO to Pin 4, MOSI to Pin 7, SCK to Pin 6, CS to Pin 5
save_to_SD = False
always_save_to_SD = False

if save_to_SD:
    spi_0 = busio.SPI(board.GP6, board.GP7, board.GP4)
    cs = board.GP5
    sd = sdcardio.SDCard(spi_0, cs)

    vfs = storage.VfsFat(sd)
    storage.mount(vfs, "/sd")

######################################################
### Set variables
######################################################
# maximum number of stored entries
max_store = 0

# Upload data to MQTT client
upload = True
## maximum connection attempts
# Internet connection
max_attempts_connect = 2
# MQTT client connection
max_attempts_mqtt = 5
# Publishing
max_attempts_publish = 2
# Maximum entries in RAM before saving to SD
max_memory_entries = 10

topic = secrets["topic"]

######################################################
### Read sensors
######################################################
datetime_format = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}"

# Run measurements and export
data_package = []
counter = -1
while True:
    counter += 1
    t_0 = localtime()
    t = datetime_format.format(*t_0)
    measurements = [t]
    for device in ow_devices:
        try:
            ds18b20 = adafruit_ds18x20.DS18X20(ow_bus, device)
            measurements.append(ds18b20.temperature)
        except:
            measurements.append(None)
            print("Failed receiving data from DS18B20 device {}.".format(device.crc))
    try:
        bme280_0 = af_bme280.Adafruit_BME280_I2C(i2c_0, 0x76)
        measurements.append(bme280_0.temperature)
        measurements.append(bme280_0.pressure)
        measurements.append(bme280_0.humidity)
    except:
        measurements.append(None)
        measurements.append(None)
        measurements.append(None)
        print("Failed receiving data from BME280 sensor 0.")
    data_package.append(measurements)
    #-----------------------------------------------------
    ## Send data
    # Scan for networks
    try_connect = 0
    while counter >= max_store and try_connect < max_attempts_connect and upload:
        try_connect += 1
        print("Publishing data... Attempt: {}".format(try_connect))
        try:
            for ap in esp.scan_networks():
                print("\t%s\t\tRSSI: %d" % (str(ap["ssid"], "utf-8"), ap["rssi"]))
        except:
            print("Network scan failed.")
        while not esp.is_connected:
            print("Connecting to AP...")
            try:
                esp.connect_AP(ssid, pw)
                print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
                print("My IP address is", esp.pretty_ip(esp.ip_address))
                #-----------------------------------------------------
                ## MiniMQTT client setup
                broker_ip = get_broker_ip()
                MQTT.set_socket(socket, esp)
                print(f"MQTT broker IP: {broker_ip}\nClient ID: {secrets['mqtt_client_id']}\n")
                mqtt_client = MQTT.MQTT(
                    broker = broker_ip,
                    port = secrets["port"],
                    username = secrets["mqtt_username"],
                    password = secrets["mqtt_key"],
                    client_id = secrets["mqtt_client_id"]
                    )
                mqtt_client.on_connect = connected
                mqtt_client.on_disconnect = disconnected
            except OSError as e:
                print("Unable to connect to AP, retrying: ", e)
                sleep(2)
        mqtt_attempt = 0
        while mqtt_attempt < max_attempts_mqtt:
            try:
                mqtt_client.connect()
                print("Connected to MQTT client.")
                break
            except:
                mqtt_attempt += 1
                print("Failed to connect to MQTT client. Attempts: {}".format(mqtt_attempt))
                sleep(2)
        if (not esp.is_connected) or (mqtt_attempt >= max_attempts_mqtt):
            print("Wifi connection lost or unable to connect to MQTT client.")
            continue
        push_attempt = 0
        while push_attempt < max_attempts_publish:
            try:
                print("Attempt publishing data package.")
                for row in data_package:
                    data = exportformat.format(*row)
                    mqtt_client.publish(topic, data)
                print("Published " + str(len(data_package)) + " entries.")
                data_package = []
                counter = -1
                break
            except:
                print("Failed to publish "  + str(len(data_package)) + " entries.")
                sleep(2)
            push_attempt += 1
            print("Publishing attempts: {}".format(push_attempt))
    # write to SD
    if (len(data_package) > max_memory_entries and save_to_SD) or always_save_to_SD:
        print("Saving data to SD card...")
        try:
            with open("/sd/data.txt", "a") as file:
                for row in data_package:
                    data = exportformat.format(*row) + "\r\n"
                    file.write(data)
            data_package = []
        except:
            print("Failed to save data to SD card.")
    if len(data_package) > 0:
        print("Data in memory.")
    sleep_interval(t_0)
