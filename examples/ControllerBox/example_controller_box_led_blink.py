"""
Controller Box LED Blink Example
--------------------------------

This example demonstrates how to control LEDs using the
ControllerBox device.

The ControllerBox manages the LED pins defined in the library
(LED_PINS) and provides simple helper functions such as:

    led_on(index)
    led_off(index)
    led_set(index, state)

Behavior:
• LED 1 (index 0) will turn ON
• Wait 0.5 seconds
• LED 1 will turn OFF
• Wait 0.5 seconds
• Repeat forever

LED index mapping:
    LED 0 -> first LED
    LED 1 -> second LED
    LED 2 -> third LED
"""

import time
from luxonis_u2if import ControllerBox


# ------------------------------------------------------------
# Connect to ControllerBox device
# ------------------------------------------------------------

box = ControllerBox()

# Initialize LEDs
box.led_init()


# ------------------------------------------------------------
# Main Loop
# ------------------------------------------------------------

while True:

    # Turn LED 1 ON (LED index 0)
    box.led_on(0)

    # Wait for 0.5 seconds
    time.sleep(0.5)

    # Turn LED 1 OFF
    box.led_off(0)

    # Wait for 0.5 seconds
    time.sleep(0.5)