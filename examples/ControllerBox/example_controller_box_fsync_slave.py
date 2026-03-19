"""
Controller Box FSYNC Configuration Example
------------------------------------------

This example demonstrates how to configure and control the
FSYNC (frame synchronization) controller using the ControllerBox.

The FSYNC controller is accessed over I2C and allows precise timing
control for synchronization signals.

Features shown in this example:

• Initialize FSYNC controller
• Set operating mode (MASTER / SLAVE)
• Configure output frequency
• Set signal polarity
• Configure duty cycle

Outputs:
    ISOLATED_STROBE  → isolated output line
    M8_FSYNC         → FSYNC signal on M8 connector

Modes:
    MASTER_INPUT     → measure incoming signal
    MASTER_OUTPUT    → generate FSYNC signal
    SLAVE            → follow external FSYNC input

In this example:
• The controller is set to SLAVE mode
• A low frequency (0.1 Hz) is configured
• Output polarity is set to LOW-active
• Duty cycle is set to 50%

Note:
Even though frequency/duty is configured, in SLAVE mode the device
primarily follows an external input signal.
"""

import time
from controller_box import ControllerBox


# ------------------------------------------------------------
# Connect to ControllerBox device
# ------------------------------------------------------------

dev = ControllerBox()


# ------------------------------------------------------------
# Initialize FSYNC controller
# ------------------------------------------------------------

# This:
# • Selects I2C bus
# • Configures bus speed
# • Detects FSYNC controller
# • Unlocks it if necessary
# • Puts it into a known default state
dev.fsync_controller_init()


# ------------------------------------------------------------
# Select FSYNC output
# ------------------------------------------------------------

# Choose which physical output to control:
# • ISOLATED_STROBE → galvanically isolated output
# • M8_FSYNC        → FSYNC on M8 connector
out = ControllerBox.FsyncOutput.ISOLATED_STROBE


# ------------------------------------------------------------
# Configure FSYNC mode
# ------------------------------------------------------------

# Set operating mode:
# • SLAVE → follow external sync signal
dev.fsync_controller_set_mode(ControllerBox.FsyncMode.SLAVE)


# ------------------------------------------------------------
# Configure FSYNC signal parameters
# ------------------------------------------------------------

# Set desired frequency (Hz)
# Note: In SLAVE mode this may be overridden by input signal
dev.fsync_controller_set_frequency(0.1)

# Set polarity:
# False → active LOW
# True  → active HIGH
dev.fsync_controller_set_polarity(False, out)

# Set duty cycle (%)
# 50% → equal HIGH/LOW time
dev.fsync_controller_set_duty_cycle(50.0, out)