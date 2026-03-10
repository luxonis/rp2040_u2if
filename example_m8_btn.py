"""
Example: Button → LED panel test

This example demonstrates how to use the RP2040_Panel helper
to control LEDs and read buttons.

Each button has a corresponding LED:

Button 0 -> LED 0
Button 1 -> LED 1
Button 2 -> LED 2

When a button is pressed, the LED turns ON.
When released, the LED turns OFF.
"""

import time
from rp2040_u2if import RP2040_u2if, RP2040_Panel

# Create RP2040 interface
rp2040 = RP2040_u2if()

# Open HID connection
rp2040.open()

# Create panel wrapper
panel = RP2040_Panel(rp2040)

# Initialize LEDs and buttons
panel.init()

print("Panel initialized")
print("Press buttons to toggle LEDs")

while True:

    # This helper automatically:
    # 1. Reads all buttons
    # 2. Updates matching LEDs
    panel.mirror_buttons_to_leds()

    # Small delay to reduce USB traffic
    time.sleep(0.05)