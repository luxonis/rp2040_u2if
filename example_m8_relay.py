"""
RP2040 Relay Control Example
----------------------------

This example demonstrates how to control the relay outputs using
the RP2040_u2if helper library.

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


# ------------------------------------------------------------
# Create RP2040 interface
# ------------------------------------------------------------

# Create the u2if helper class
rp2040 = RP2040_u2if()

# Open the HID connection to the RP2040 device
rp2040.open()


# ------------------------------------------------------------
# Initialize indicator LED
# ------------------------------------------------------------

# Configure GPIO17 as an output for a status LED
rp2040.gpio_init_pin(
    17,
    RP2040_u2if.GPIO_OUT,
    RP2040_u2if.GPIO_PULL_NONE
)


# ------------------------------------------------------------
# Initialize relay control pins
# ------------------------------------------------------------

# Configure all relay GPIO pins used internally by the library
rp2040.relay_init()


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
        rp2040.gpio_set_pin(17, 1)

        # Send SET pulse to the relay
        rp2040.relay_set(relay)

        # Wait before resetting
        time.sleep(0.5)

        # ----------------------------------------------------
        # Deactivate relay
        # ----------------------------------------------------

        print("Relay", relay, "RESET")

        # Turn LED OFF
        rp2040.gpio_set_pin(17, 0)

        # Send RESET pulse to the relay
        rp2040.relay_reset(relay)

        # Wait before moving to the next relay
        time.sleep(0.5)