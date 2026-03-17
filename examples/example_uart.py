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

Configuration:
    UART must be explicitly selected (0 or 1).
"""

import time
from luxonis_u2if import RP2040_u2if


# ------------------------------------------------------------
# Create RP2040 interface
# ------------------------------------------------------------

dev = RP2040_u2if()
dev.open()


# ------------------------------------------------------------
# UART configuration
# ------------------------------------------------------------

UART_PORT = 1


# ------------------------------------------------------------
# Initialize UART
# ------------------------------------------------------------

dev.uart_init(UART_PORT, 115200)


# ------------------------------------------------------------
# Clear any existing UART data
# ------------------------------------------------------------

dev.uart_read(UART_PORT)


# ------------------------------------------------------------
# Send data over UART
# ------------------------------------------------------------

dev.uart_write(UART_PORT, b"hello\n")


# ------------------------------------------------------------
# Read UART response
# ------------------------------------------------------------

data = dev.uart_read(UART_PORT)

print(data)