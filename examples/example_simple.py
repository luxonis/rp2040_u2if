import time
from luxonis_u2if import RP2040_u2if

rp2040 = RP2040_u2if()
rp2040.open()

rp2040.gpio_init_pin(17, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)

while True:

    rp2040.gpio_set_pin(17, 1)
    time.sleep(0.5)
    rp2040.gpio_set_pin(17, 0)
    time.sleep(0.5)