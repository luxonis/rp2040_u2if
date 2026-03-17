"""
Controller Box Button and LED Example
------------------------------------

This example demonstrates how to use the ControllerBox device
to control LEDs using button events.

Each button has a corresponding LED:

Button 1 -> LED 0
Button 2 -> LED 1
Button 3 -> LED 2

When a button is pressed, the LED turns ON.
When released, the LED turns OFF.
"""

import time
from luxonis_u2if import ControllerBox


# ------------------------------------------------------------
# Connect to ControllerBox device
# ------------------------------------------------------------

# Create the ControllerBox device
box = ControllerBox()


# ------------------------------------------------------------
# Initialize LEDs
# ------------------------------------------------------------
box.led_init()


# ------------------------------------------------------------
# Button callback
# ------------------------------------------------------------

def button_cb(btn, state):
    """
    Button event callback.

    Parameters
    ----------
    btn : int
        Button index (1..3)
    state : bool
        True = pressed
        False = released
    """
    box.led_set(btn, state)


# Register callback
box.set_btn_callback(button_cb)


print("ControllerBox ready")
print("Press buttons to control LEDs")


# ------------------------------------------------------------
# Main loop
# ------------------------------------------------------------

# Nothing required here — events are handled in background
while True:
    time.sleep(1)