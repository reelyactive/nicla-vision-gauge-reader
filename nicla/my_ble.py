# This example demonstrates a simple temperature sensor peripheral.
#
# The sensor's local value updates every second, and it will notify
# any connected central every 10 seconds.
# Comment

import bluetooth
import random
import struct
import time
from ble_advertising import advertising_payload
from machine import LED
from micropython import const




ble = bluetooth.BLE()
ble.active(True)




def send_value(value):
    # value is a percentage
    # we want a hex value btw 0 and 65535,
    # then split into TWO 16 byte values (higher and lower)
    bitvalue = int(value * .01 * 65535)
    high = (bitvalue >> 8)
    low = (bitvalue & 0x00FF)
    print("sending: ", value, bitvalue, hex(bitvalue), hex(high), hex(low), high, low )
    # Advertising payload bytes:
    # 0:   0x05 = Length (not including the length byte itself)
    # 1:   0x16 = 16-bit service data (from GAP)
    # 2-3: 0x2af9 = 16-bit UUID of generic level characteristic (little endian)
    # 4-5: 0x1234 = 16-bit generic level value (little endian) 4660 / 65535 = 7.11%
    #_ADV_PAYLOAD = [ 0x05, 0x16, 0xf9, 0x2a, 0x34, 0x12 ]
    _ADV_PAYLOAD = [ 0x05, 0x16, 0xf9, 0x2a, low, high ]
    _ADV_INTERVAL_US = 500000 # 500000 microseconds = .5 seconds
    ble.gap_advertise(_ADV_INTERVAL_US, adv_data=bytearray(_ADV_PAYLOAD))
