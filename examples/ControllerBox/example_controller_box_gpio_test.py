"""
Controller Box GPIO Sequential Hardware Tester
-----------------------------------------------

Tests logical GPIO pins by generating a random digital signal on each pin
and verifying it on a fixed input pin.

This example validates the GPIO remapping implemented in ControllerBox.

When prompted, connect the input pin to the pin currently being tested.

Example:
Connect GPIO1 -> GPIO2

The script sends random HIGH/LOW signals and checks if the input follows.

A PASS occurs when a sequence of matching signals is detected.
"""

import time
import random
import sys
from luxonis_u2if import ControllerBox


# ------------------------------------------------------------
# Connect to ControllerBox device
# ------------------------------------------------------------

box = ControllerBox()


# ------------------------------------------------------------
# Test configuration
# ------------------------------------------------------------

# Logical GPIO pins to test (these use the ControllerBox remap)
test_pins = list(range(1, 17))

# Logical input pin used for verification
input_pin = 1

# Number of consecutive matches required for PASS
length_of_roll = 10


# Initialize input pin
box.gpio_init(input_pin, box.GPIO_IN, box.GPIO_PULL_DOWN)


# ------------------------------------------------------------
# Helper display
# ------------------------------------------------------------

def print_rolls(out_rolls, in_rolls):

    sys.stdout.write(
        "\rOUT: " + " ".join(str(v) for v in out_rolls) +
        "   IN: " + " ".join(str(v) for v in in_rolls)
    )
    sys.stdout.flush()


# ------------------------------------------------------------
# Main test loop
# ------------------------------------------------------------

for pin in test_pins:

    if pin == input_pin:
        continue

    box.gpio_init(pin, box.GPIO_OUT, box.GPIO_PULL_NONE)
    box.gpio_set(pin, 0)

    print(f"\nConnect GPIO{input_pin} to GPIO{pin}")

    out_rolls = [1] * length_of_roll
    in_rolls = [0] * length_of_roll

    matches = 0

    while True:

        value = random.randint(0, 1)
        box.gpio_set(pin, value)

        time.sleep(0.2)

        read = 1 if box.gpio_get(input_pin) else 0

        out_rolls.append(value)
        in_rolls.append(read)

        if len(out_rolls) > length_of_roll:
            out_rolls.pop(0)
            in_rolls.pop(0)

        print_rolls(out_rolls, in_rolls)

        if read == value:
            matches += 1
        else:
            matches = 0

        if matches >= length_of_roll and not (
            all(v == 0 for v in out_rolls) or
            all(v == 1 for v in out_rolls)
        ):
            print(f"  -> PASS (GPIO{pin})")
            break

    box.gpio_set(pin, 0)


print("\nAll GPIO tests finished.")