"""
Controller Box Relay Control Example
------------------------------------

This example demonstrates how to control the relay outputs using
the ControllerBox helper wrapper.

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
# Create controller box wrapper
# ------------------------------------------------------------

box = ControllerBox(rp2040)


# ------------------------------------------------------------
# Initialize indicator LED
# ------------------------------------------------------------

# Configure GPIO17 as an output for a status LED
box.gpio_init(
    17,
    rp2040.GPIO_OUT,
    rp2040.GPIO_PULL_NONE
)


# ------------------------------------------------------------
# Initialize relay control pins
# ------------------------------------------------------------

# Configure all relay GPIO pins
box.relay_init()

# Configure panel
box.panel_init()


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