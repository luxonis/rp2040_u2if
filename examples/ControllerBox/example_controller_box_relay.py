"""
Controller Box Relay Control Example
------------------------------------

This example demonstrates how to control the relay outputs using
the ControllerBox device.

The firmware exposes 4 relays which can be controlled using:

    relay_set(relay_number)
    relay_reset(relay_number)

Relay numbers are:
    1, 2, 3, 4

Behavior:
• Each relay is SET (activated)
• Then RESET (deactivated)
• An LED on GPIO17 indicates relay activity

The example cycles through all relays continuously.
"""

import time
from luxonis_u2if import ControllerBox


# ------------------------------------------------------------
# Connect to ControllerBox device
# ------------------------------------------------------------

box = ControllerBox()


# ------------------------------------------------------------
# Initialize relay control pins
# ------------------------------------------------------------

# Configure all relay GPIO pins
box.relay_init()

# Configure  LED
box.led_init()


# ------------------------------------------------------------
# Main Loop
# ------------------------------------------------------------

while True:

    # Cycle through all 4 relays
    for relay in range(1, 5):

        # ----------------------------------------------------
        # Activate relay
        # ----------------------------------------------------

        print("Relay", relay, "SET")

        # Turn LED ON to indicate relay activity
        box.led_on(0)
        # Send SET pulse to the relay
        box.relay_set(relay)

        # Wait before resetting
        time.sleep(0.5)

        # ----------------------------------------------------
        # Deactivate relay
        # ----------------------------------------------------

        print("Relay", relay, "RESET")

        # Turn LED OFF
        box.led_off(0)

        # Send RESET pulse to the relay
        box.relay_reset(relay)

        # Wait before moving to the next relay
        time.sleep(0.5)