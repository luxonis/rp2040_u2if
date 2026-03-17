"""
Controller Box Serial Example
-----------------------------

This example demonstrates how to use the Controller Box serial
interface.

The serial interface is connected to the RS-232 port of the
Controller Box.

Behavior:
• Initialize the serial port at 115200 baud
• Send a message
• Wait for a response
• Print received data
"""

import time
from luxonis_u2if import ControllerBox


# ------------------------------------------------------------
# Connect to ControllerBox device
# ------------------------------------------------------------

box = ControllerBox()


# ------------------------------------------------------------
# Initialize serial port
# ------------------------------------------------------------

print("Initializing serial interface (115200 baud)...")
box.serial_init(115200)

# Clear any startup garbage
box.serial_read()

print("Serial ready\n")


# ------------------------------------------------------------
# Main Loop
# ------------------------------------------------------------

while True:

    message = "hello"

    # Send message
    print(f'Sent: "{message}"')
    box.serial_write(message + "\n")

    # Wait for response
    print("Waiting for response...")

    time.sleep(0.5)

    # Read response
    data = box.serial_read()

    if data:
        try:
            decoded = data.decode().strip()
        except:
            decoded = data

        print(f'Received: "{decoded}"\n')
    else:
        print("No response received\n")

    time.sleep(3)