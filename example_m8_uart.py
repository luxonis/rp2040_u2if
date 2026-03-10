"""
RP2040 UART Example
-------------------

This example demonstrates how to use the UART interface through
the RP2040_u2if helper library.

The library communicates with the RP2040 over USB HID while
the RP2040 forwards UART traffic to the physical UART pins.

Behavior:
• Initialize UART at 115200 baud
• Flush any startup garbage from the UART buffer
• Send the message "hello"
• Read back any received UART data

Default configuration:
    UART1 is used unless another UART is specified.
"""

import time
from rp2040_u2if import RP2040_u2if


# ------------------------------------------------------------
# Create RP2040 interface
# ------------------------------------------------------------

# Create the u2if helper class
dev = RP2040_u2if()

# Open the HID connection to the RP2040 device
dev.open()


# ------------------------------------------------------------
# Initialize UART
# ------------------------------------------------------------

# Initialize UART1 at 115200 baud
# (UART1 is the default if no UART index is provided)
dev.uart_init(115200)


# ------------------------------------------------------------
# Clear any existing UART data
# ------------------------------------------------------------

# Sometimes devices send startup messages or noise.
# This clears any existing data in the buffer.
dev.uart_read()


# ------------------------------------------------------------
# Send data over UART
# ------------------------------------------------------------

# Write a test message to the UART port
dev.uart_write(b"hello\n")


# ------------------------------------------------------------
# Read UART response
# ------------------------------------------------------------

# Read all available UART data
data = dev.uart_read()

# Print the received bytes
print(data)