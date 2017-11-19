from utime import sleep

from machine import Pin
from neopixel import NeoPixel
import network

# The CPython "colorsys" module must be loaded onto the device (see
# https://raw.githubusercontent.com/python/cpython/master/Lib/colorsys.py).
from colorsys import hsv_to_rgb


# The access point names to monitor.
MONITORED_WIFI_SSIDS = (b'ccooper',)

# The range of expected RF signal strengths (see
# https://en.wikipedia.org/wiki/Received_signal_strength_indication).
RSSI_MIN, RSSI_MAX = -80, -30

# Initialize the wi-fi client interface (i.e. the station interface).
station_if = network.WLAN(network.STA_IF)
station_if.active(True)

# Setup the pins and NeoPixels.
pin_numbers = (5, 4, 14, 12, 13, 15)
pins = [Pin(pin_number, Pin.OUT) for pin_number in pin_numbers]
neopixels = [NeoPixel(pin, 40) for pin in pins]


# RF signal strengths are distributed on a one-dimensional scale.  The more
# negative the signal strength, the weaker the RF signal is.  To drive a RGB
# LED, a signal strength must be mapped to the three-dimensional RGB color
# space.  This is most easily done by scaling the signal strength within a
# defined range, and then using the HSV to RGB color mapping algorithm, where
# the scaled signal strength is treated as the hue (see
# https://en.wikipedia.org/wiki/HSL_and_HSV).  The last sixth of the color
# wheel is ignored as to avoid the color wrapping around and making the best
# and worst signals appear as the same color.
def rssi_to_rgb(rssi):
    scaled_rssi = (rssi - RSSI_MIN) / (RSSI_MAX - RSSI_MIN)
    scaled_rssi = min(1.0, max(0.0, scaled_rssi))
    scaled_rssi *= 5 / 6

    rgb_tuple = hsv_to_rgb(scaled_rssi, 1.0, 1.0)
    rgb_tuple = tuple(int(127 * element) for element in rgb_tuple)

    print('rssi = %d, scaled_rssi = %f, rgb_tuple = %s'
          % (rssi, scaled_rssi, rgb_tuple))

    return rgb_tuple


# The main loop continuously performs the following steps:
#     - Scan for wi-fi access points with one of the defined names.
#     - Calculate the greatest RF signal strength.
#     - Convert the RF signal strength to a RGB tuple.
#     - Send the RGB tuple to the NeoPixels.
while True:
    access_points = station_if.scan()
    access_points = [access_point for access_point in access_points
                     if access_point[0] in MONITORED_WIFI_SSIDS]

    rssi = RSSI_MIN
    if access_points:
        rssi = max([access_point[3] for access_point in access_points])

    rgb_tuple = rssi_to_rgb(rssi)

    for neopixel in neopixels:
        neopixel.fill(rgb_tuple)
    for neopixel in neopixels:
        neopixel.write()

    # Control must be periodically yielded as to reset the watchdog timer.
    sleep(0)
