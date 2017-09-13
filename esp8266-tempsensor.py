"""
modified from original tutorial at http://docs.micropython.org/en/v1.8.2/esp8266/esp8266/tutorial/onewire.html
https://github.com/micropython/micropython/tree/master/drivers/onewire

Seems like the DS18B20 class has been moved to its own library (hence import ds18x20), while the tutorial hasn't
been updated.
"""

import onewire
import ds18x20
from machine import I2C, Pin
from esp8266_i2c_lcd import I2cLcd
from time import sleep_ms, ticks_ms

### temp sensor on D3/GPIO0
pin = Pin(0)
# create the sensor object
sensor = ds18x20.DS18X20(onewire.OneWire(pin))
# scan for devices on the port
roms = sensor.scan()
print("found 1wire devices:", roms)

### LCD setup
i2c = I2C(scl=Pin(5), sda=Pin(4), freq=400000)
# scan for the i2c device - only one connected at the moment
lcd_id = i2c.scan()[0]
print("found i2c devices:", lcd_id)
#create the LCD object
lcd = I2cLcd(i2c, lcd_id, 2, 16)

# read temperature and print to LCD until forever
while True:
    print("temp is...:", end=" ")
    sensor.convert_temp()
    sleep_ms(750)
    temp = sensor.read_temp(roms[0])
    print(temp, end=" ")
    temp = round(temp, 2)
    print()
    lcd.clear()
    lcd.putstr("temp:" + str(temp))
    sleep_ms(30000)

