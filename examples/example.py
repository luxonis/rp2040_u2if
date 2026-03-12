import time
from rp2040_u2if import RP2040_u2if

# Modify serial to correspond with the device in question
DEVICE_SERIAL_1 = '0x...'
DEVICE_SERIAL_2 = '0x...'

rp2040_1 = RP2040_u2if()
rp2040_2 = RP2040_u2if()

rp2040_1.open(51966, 16389, DEVICE_SERIAL_1)
rp2040_2.open(51966, 16389, DEVICE_SERIAL_2)

rp2040_1.gpio_init_pin(17, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)
rp2040_2.gpio_init_pin(17, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)

while True:
    rp2040_1.gpio_set_pin(17, 0)
    rp2040_2.gpio_set_pin(17, 0)
    time.sleep(0.5)
    rp2040_1.gpio_set_pin(17, 1)
    rp2040_2.gpio_set_pin(17, 1)
    time.sleep(0.5)
