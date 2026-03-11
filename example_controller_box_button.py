"""
Controller Box Button and LED Example
------------------------------------

This example demonstrates how to use the ControllerBox helper
to control LEDs and read buttons.

Each button has a corresponding LED:

Button 0 -> LED 0
Button 1 -> LED 1
Button 2 -> LED 2

When a button is pressed, the LED turns ON.
When released, the LED turns OFF.
"""

import time
from rp2040_u2if import RP2040_u2if
from controller_box import ControllerBox


# Create RP2040 interface
rp2040 = RP2040_u2if()

# Open HID connection
rp2040.open()

# Create controller box wrapper
box = ControllerBox(rp2040)

# Initialize LEDs and buttons
box.panel_init()

print("Panel initialized")
print("Press buttons to toggle LEDs")


while True:

    # Update button states
    box.panel_scan()

    # Mirror buttons to LEDs
    box.mirror_buttons_to_leds()

    # Small delay to reduce USB traffic
    time.sleep(0.05)