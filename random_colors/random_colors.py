from urandom import getrandbits
from utime import sleep

from machine import Pin
from neopixel import NeoPixel


# ONE-TIME: Setup the pins and NeoPixels.
pin_numbers = (5, 4, 14, 12, 13, 15)
pins = [Pin(pin_number, Pin.OUT) for pin_number in pin_numbers]
neopixels = [NeoPixel(pin, 40) for pin in pins]

# REPEAT FOREVER: Generate a random RGB tuple, where each element is from 0 to
# 127, and send it to the NeoPixels.  NeoPixels support 24-bit color, but
# using 7-bits per color limits their current usage (i.e. their amperage).
while True:
    rgb_tuple = tuple(getrandbits(7) for _ in range(3))
    for neopixel in neopixels:
        neopixel.fill(rgb_tuple)
    for neopixel in neopixels:
        neopixel.write()

    sleep(3)
