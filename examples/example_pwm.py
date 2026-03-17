import time
from luxonis_u2if import RP2040_u2if

rp2040 = RP2040_u2if()
rp2040.open()

rp2040.gpio_init_pin(14, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)

def duty_cycle_int_from_percent(duty_cycle_percent: float):
    duty_cycle_int = int(round(duty_cycle_percent / 100.0 * 65535))
    return duty_cycle_int

pwm_pin = 14
frequency = 1250
duty_cycle_percent = 50

while True:
    duty_cycle_int = duty_cycle_int_from_percent(duty_cycle_percent)
    rp2040.pwm_configure(pwm_pin, 1250, duty_cycle_int)
    time.sleep(2)

    rp2040.pwm_deinit(pwm_pin)
    time.sleep(2)