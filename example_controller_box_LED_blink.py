"""
Controller Box LED Blink Example
--------------------------------

This example demonstrates how to control LEDs using the
ControllerBox helper wrapper.

The ControllerBox manages the LED pins defined in the library
(PANEL_LED_PINS) and provides simple helper functions such as:

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
    LED 0 -> first LED in PANEL_LED_PINS
    LED 1 -> second LED
    LED 2 -> third LED
"""

import time
from rp2040_u2if import RP2040_u2if
from controller_box import ControllerBox


# ------------------------------------------------------------
# Create RP2040 interface
# ------------------------------------------------------------

# Create the u2if helper class
rp2040 = RP2040_u2if()

# Open the HID connection to the RP2040 device
rp2040.open()


# ------------------------------------------------------------
# Create and initialize the controller box helper
# ------------------------------------------------------------

# Create the ControllerBox wrapper
box = ControllerBox(rp2040)

# Initialize panel GPIO pins (LEDs and buttons)
box.panel_init()


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