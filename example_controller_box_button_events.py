"""
Controller Box Button Event Example
-----------------------------------

This example demonstrates how to detect button events using the
ControllerBox panel interface.

Each button has a corresponding LED:

Button 0 -> LED 0
Button 1 -> LED 1
Button 2 -> LED 2

When a button is pressed:
• The corresponding LED turns ON
• The terminal updates the button state to "Toggled"

When a button is released:
• The LED turns OFF
• The terminal updates the button state to "Not Toggled"

The terminal display updates in place whenever a button state changes.
"""

import time
from rp2040_u2if import RP2040_u2if
from controller_box import ControllerBox


# ------------------------------------------------------------
# Create RP2040 interface
# ------------------------------------------------------------

rp2040 = RP2040_u2if()
rp2040.open()

box = ControllerBox(rp2040)

# Initialize panel hardware
box.panel_init()


# ------------------------------------------------------------
# Terminal UI
# ------------------------------------------------------------

button_states = ["Not Toggled"] * 3

# Print header
print("Button 1        Button 2        Button 3")

def print_states():
    """Print button states on one terminal line."""
    line = ""
    for state in button_states:
        line += f"{state:<15}"
    print("\r" + line, end="  ", flush=True)


print_states()


# ------------------------------------------------------------
# Main Loop
# ------------------------------------------------------------

while True:

    # Update button states
    box.panel_scan()

    for i in range(3):

        # Button pressed event
        if box.button_pressed_event(i):

            box.led_on(i)
            button_states[i] = "  Toggled  "
            print_states()

        # Button released event
        elif box.button_released_event(i):

            box.led_off(i)
            button_states[i] = "Not Toggled"
            print_states()

    time.sleep(0.02)