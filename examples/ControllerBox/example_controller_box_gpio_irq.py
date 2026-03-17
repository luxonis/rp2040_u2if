"""
Controller Box GPIO IRQ Example
-------------------------------

Demonstrates how to read button events directly from GPIO IRQ.
"""

import time
from luxonis_u2if import ControllerBox


box = ControllerBox()

BUTTON_PIN = 20


# Configure button
box.gpio_init(BUTTON_PIN, box.GPIO_IN, box.GPIO_PULL_UP)

# Enable interrupts
box.gpio_set_irq(
    BUTTON_PIN,
    box.IRQ_RISING | box.IRQ_FALLING,
    debounce=True
)

print("Waiting for button events...\n")


while True:

    for pin, event in box.gpio_get_irq():

        if pin != BUTTON_PIN:
            continue

        if event == box.IRQ_FALLING:
            print("Button 1 pressed")

        elif event == box.IRQ_RISING:
            print("Button 1 released")

    time.sleep(0.01)