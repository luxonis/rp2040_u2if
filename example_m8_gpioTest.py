"""
RP2040 GPIO Sequential Hardware Tester
--------------------------------------

Tests GPIO pins by generating a random digital signal on each pin and
verifying it on a fixed input pin.

Connect the input pin to the pin being tested when prompted.
"""

import time
import random
import sys
from rp2040_u2if import RP2040_u2if


# ------------------------------------------------------------
# Initialize RP2040
# ------------------------------------------------------------

rp2040 = RP2040_u2if()
rp2040.open()


# ------------------------------------------------------------
# Test configuration
# ------------------------------------------------------------

# GPIO pins to test
test_pins = list(range(1, 17))

# Input pin used for verification
input_pin = 1

# Number of consecutive matches required for PASS
length_of_roll = 10


# Initialize input pin
rp2040.gpio_init_pin(input_pin, RP2040_u2if.GPIO_IN, RP2040_u2if.GPIO_PULL_DOWN)


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

    rp2040.gpio_init_pin(pin, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)
    rp2040.gpio_set_pin(pin, 0)

    print(f"\nConnect GPIO{input_pin} to GPIO{pin}")

    out_rolls = [1] * length_of_roll
    in_rolls = [0] * length_of_roll

    matches = 0

    while True:

        value = random.randint(0, 1)
        rp2040.gpio_set_pin(pin, value)

        time.sleep(0.2)

        read = 1 if rp2040.gpio_get_pin(input_pin) else 0

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

    rp2040.gpio_set_pin(pin, 0)


print("\nAll GPIO tests finished.")