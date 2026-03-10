```python
"""
RP2040 GPIO Sequential Hardware Tester
--------------------------------------

This script verifies that individual GPIO pins on an RP2040 board are
electrically working by generating a random digital signal on each pin
and checking that the same signal appears on a designated input pin.

Test Method
-----------
1. The program selects a GPIO pin from the test list.
2. It asks the user to connect that pin to the input test pin.
3. The tested pin outputs a random sequence of 0/1 values.
4. The input pin reads the signal.
5. The program compares the two sequences.
6. If they match for N consecutive samples (length_of_roll) and the
   sequence is not constant (all 0s or all 1s), the pin is marked PASS.

Why constant sequences are rejected
-----------------------------------
If the input pin is accidentally tied to GND or 3.3V, the signal would
always read 0 or 1 and could falsely pass. Rejecting constant sequences
prevents this failure mode.

Display
-------
The terminal shows the last N generated values (OUT) and the values read
from the input pin (IN). The line is continuously overwritten so the
display stays compact and easy to read.

Hardware setup
--------------
Connect the currently tested GPIO pin to the input test pin when prompted.

Example:
    Connect GPIO27 to GPIO5

The script will then generate a signal on GPIO5 and verify it on GPIO27.

Configuration
-------------
test_pins      : GPIO pins to be tested
input_pin      : GPIO used for reading the signal
length_of_roll : Number of consecutive matching samples required for PASS
"""

import time
import random
import sys
from rp2040_u2if import RP2040_u2if


# ------------------------------------------------------------
# Initialize RP2040 interface
# ------------------------------------------------------------
rp2040 = RP2040_u2if()
rp2040.open()


# ------------------------------------------------------------
# Test configuration
# ------------------------------------------------------------

# Pins that will be tested sequentially
test_pins = list(range(1, 15))

# Input pin used to read the generated signal
input_pin = 1

# Number of consecutive matching samples required to pass
length_of_roll = 10


# Initialize the input pin
rp2040.gpio_init_pin(input_pin, RP2040_u2if.GPIO_IN, RP2040_u2if.GPIO_PULL_NONE)


# ------------------------------------------------------------
# Helper function: display rolling sequences
# ------------------------------------------------------------
def print_rolls(out_rolls, in_rolls):
    """
    Prints the current rolling sequences of generated (OUT) and
    measured (IN) values on a single terminal line.

    The carriage return ('\\r') moves the cursor back to the
    start of the line so the output overwrites itself.
    """
    sys.stdout.write(
        "\rOUT: " + " ".join(str(v) for v in out_rolls) +
        "   IN: " + " ".join(str(v) for v in in_rolls)
    )
    sys.stdout.flush()


# ------------------------------------------------------------
# Main GPIO testing loop
# ------------------------------------------------------------
for pin in test_pins:

    # Configure current pin as output
    rp2040.gpio_init_pin(pin, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)
    rp2040.gpio_set_pin(pin, 0)

    print(f"\nConnect GPIO{input_pin} to GPIO{pin}")

    # Initialize rolling buffers
    # OUT is pre-filled with 1s to avoid accidental "all-zero" startup patterns
    out_rolls = [1] * length_of_roll
    in_rolls = [0] * length_of_roll

    matches = 0

    while True:

        # Generate random output value
        value = random.randint(0, 1)
        rp2040.gpio_set_pin(pin, value)

        # Wait before sampling input
        time.sleep(0.2)

        # Read the input pin
        read = 1 if rp2040.gpio_get_pin(input_pin) else 0

        # Update rolling buffers
        out_rolls.append(value)
        in_rolls.append(read)

        if len(out_rolls) > length_of_roll:
            out_rolls.pop(0)
            in_rolls.pop(0)

        # Update terminal display
        print_rolls(out_rolls, in_rolls)

        # Track consecutive matches
        if read == value:
            matches += 1
        else:
            matches = 0

        # PASS condition:
        #  - enough consecutive matches
        #  - sequence is not constant (protects against GND/3V3 tie)
        if matches >= length_of_roll and not (
            all(v == 0 for v in out_rolls) or
            all(v == 1 for v in out_rolls)
        ):
            print(f"  -> PASS (GPIO{pin})")
            break

    # Reset tested pin after finishing
    rp2040.gpio_set_pin(pin, 0)


print("\nAll GPIO tests finished.")
```
