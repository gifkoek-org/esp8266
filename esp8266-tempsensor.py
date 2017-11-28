"""
modified from original tutorial at http://docs.micropython.org/en/v1.8.2/esp8266/esp8266/tutorial/onewire.html
https://github.com/micropython/micropython/tree/master/drivers/onewire

Seems like the DS18B20 class has been moved to its own library (hence import ds18x20), while the tutorial hasn't
been updated.

using the LCD library from https://github.com/dhylands/python_lcd

"""

import onewire
import ds18x20
from machine import I2C, Pin
from esp8266_i2c_lcd import I2cLcd
from time import sleep_ms, ticks_ms
import network
import urequests

def start_tempsensor(pin_number):

    # create the pin object
    pin = Pin(pin_number)
    # create the sensor object
    sensor = ds18x20.DS18X20(onewire.OneWire(pin))
    # scan for devices on the port
    roms = sensor.scan()
    print("found 1wire devices:", roms)

    # assume only one device for now, hence index 0
    return sensor, roms[0]

def start_lcd(sclpin, sdapin):
    ### LCD setup
    i2c = I2C(scl=Pin(sclpin), sda=Pin(sdapin), freq=400000)
    # scan for the i2c device - only one connected at the moment
    lcd_id = i2c.scan()[0]
    print("found i2c devices:", lcd_id)
    #create the LCD object
    lcd = I2cLcd(i2c, lcd_id, 2, 16)

    return lcd

def start_wifi():
    ### setup wifi
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect("SSID here", "passwordhere")
    # wait for wifi to connect...
    while not wifi.isconnected():
        print("starting wifi...")
        sleep_ms(1000)
    print(wifi.ifconfig())


def get_temp(tempsensor):
    print("temp is...:", end=" ")
    tempsensor.convert_temp()
    sleep_ms(750)
    temp = tempsensor.read_temp(id)
    print(temp, end=" ")

    return temp


# initialise hardware
start_wifi()
tempsensor, id = start_tempsensor(0)     # 0 = D3/GPIO0
lcd = start_lcd(5, 4)                   # 5 = D0/GPIO5, 4 = D1/GPIO4

# read temperature and print to LCD until forever
while True:
    temp = round(get_temp(tempsensor), 2)
    print()
    lcd.clear()
    lcd.putstr("temp:" + str(temp))
    sleep_ms(30000)
