import network
ap_if = network.WLAN(network.AP_IF)
ap_if.active(False)
sta_if = network.WLAN(network.STA_IF)
sta_if.active(False)

from machine import Pin
from neopixel import NeoPixel
pin_numbers = (5, 4, 14, 12, 13, 15)
pins = [Pin(pin_number, Pin.OUT) for pin_number in pin_numbers]
neopixels = [NeoPixel(pin, 40) for pin in pins]
for neopixel in neopixels:
    neopixel.fill((0,0,0))
for neopixel in neopixels:
    neopixel.write()

from utime import sleep
sleep(10)

import random_colors
