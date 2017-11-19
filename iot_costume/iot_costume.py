from ubinascii import hexlify
from urandom import getrandbits
import usocket
from utime import sleep, ticks_ms

from machine import Pin
from neopixel import NeoPixel
import network

from umqtt.simple import MQTTClient
from websocket import websocket


# The wi-fi access point SSID and password.
WIFI_AP_SSID = b'ccooper'
WIFI_AP_PASSWORD = b'pytexas_2017'

# Initialize the wi-fi client interface (i.e. the station interface) and
# connect to the defined access point.
station_if = network.WLAN(network.STA_IF)
station_if.active(True)
station_if.connect(WIFI_AP_SSID, WIFI_AP_PASSWORD)

# Setup the pins and NeoPixels.
pin_numbers = (5, 4, 14, 12, 13, 15)
pins = [Pin(pin_number, Pin.OUT) for pin_number in pin_numbers]
neopixels = [NeoPixel(pin, 40) for pin in pins]

# Publish messages to and receive messages from the MQTT broker forever.
keepalive = 60
connected = False
topic = b'costume/1'
last_ping, last_publish = 0, 0
while True:
    if not connected:
        print('Connecting...')

        # Create a TCP socket and connect it to the MQTT broker.  If the
        # connection attempt fails, wait a little and try again.
        s = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        try:
            addr = usocket.getaddrinfo(b'broker.mqttdashboard.com', 8000)[0]
            s.connect(addr[-1])
        except OSError:
            s.close()
            sleep(3)
            continue

        # Negotiate the WebSocket protocol upgrade via HTTP.  This is most
        # easily done by simulating an HTTP request with the necessary
        # headers.  There is no need to bust out a full HTTP implementation.
        #
        # TODO: Generate the value for the "Sec-WebSocket-Key" header
        # dynamically.
        s.write((b'GET /mqtt HTTP/1.1\r\n'
                 b'Host: broker.mqttdashboard.com\r\n'
                 b'Connection: Upgrade\r\n'
                 b'Upgrade: websocket\r\n'
                 b'Sec-WebSocket-Key: aSk+xCH/A9ZbxvqjxF8itg==\r\n'
                 b'Sec-WebSocket-Version: 13\r\n'
                 b'Sec-Websocket-Protocol: mqtt\r\n'
                 b'\r\n'))

        # TODO: Validate the response to the websocket upgrade request.  This
        # can be done by checking the HTTP response code and validating the
        # "Sec-WebSocket-Accept" header.
        line = s.readline()
        while line:
            if line == b'\r\n':
                break
            line = s.readline()

        # Now that the WebSocket protocol upgrade negotiation is complete,
        # create a WebSocket from the TCP socket connected to the MQTT broker.
        ws = websocket(s, is_client=True)

        # Create an MQTT client.
        client_id = hexlify(bytes([getrandbits(8) for _ in range(8)]))
        client = MQTTClient(client_id, sock=ws, keepalive=keepalive)

        # This is the callback function that is invoked when a message is
        # received.  It parses the message looking for a valid RGB tuple, and
        # sends it to the NeoPixels.
        def on_message_received(topic, message):
            print('Message received: topic=%s, message=%s' % (topic, message))
            message = message.decode('ascii')
            elements = message.split(':')
            if len(elements) == 2 and elements[0] == 'C':
                rgb_tuple = elements[1]
                rgb_tuple = rgb_tuple.split(',')
                try:
                    rgb_tuple = tuple(int(element) for element in rgb_tuple)
                except ValueError:
                    pass
                else:
                    rgb_tuple = tuple(max(0, min(127, element))
                                      for element in rgb_tuple)
                    print('rgb_tuple = %s' % (rgb_tuple,))
                    for neopixel in neopixels:
                        neopixel.fill(rgb_tuple)
                    for neopixel in neopixels:
                        neopixel.write()

        # Set the message receipt callback function
        client.set_callback(on_message_received)

        # Perform the MQTT connection handshake.
        client.connect()
        connected = True
        last_publish = 0
        last_ping = ticks_ms()
        print('Connected')

        print('Subscribing to topic %s...' % topic)
        client.subscribe(topic)
        print('Subscribed')

    else:

        # Periodically ping the broker consistently with the "keepalive"
        # argument used when connecting.  If this isn't done, the broker will
        # disconnect when the client has been idle for 1.5x the keepalive
        # time.
        if ticks_ms() - last_ping >= keepalive * 1000:
            client.ping()
            last_ping = ticks_ms()

    # Every two minutes publish a message for fun.
    if ticks_ms() - last_publish >= 2 * 60 * 1000:
        message = b'ticks_ms() = %d' % ticks_ms()
        print('Publishing to topic %s message %s...' % (topic, message))
        client.publish(topic, message)
        last_publish = ticks_ms()
        print('Published')

    # Receive the next message if one is available, and handle the case that
    # the broker has disconnected.
    try:
        client.check_msg()
    except OSError as e:
        if e.args[0] == -1:
            ws.close()
            connected = False
            print('Connection closed')
            continue

    # Sleep a little to not needlessly burn processor cycles.
    sleep(0.5)
