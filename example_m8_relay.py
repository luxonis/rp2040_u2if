import time
from rp2040_u2if import RP2040_u2if

rp2040 = RP2040_u2if()
rp2040.open()

# LED
rp2040.gpio_init_pin(17, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)

# Init relays
rp2040.relay_init()

while True:

    for relay in range(1,5):

        print("Relay", relay, "SET")
        rp2040.gpio_set_pin(17,1)
        rp2040.relay_set(relay)

        time.sleep(0.5)

        print("Relay", relay, "RESET")
        rp2040.gpio_set_pin(17,0)
        rp2040.relay_reset(relay)

        time.sleep(0.5)
