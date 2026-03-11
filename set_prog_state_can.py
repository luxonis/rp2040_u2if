import time
from sys import argv
from rp2040_u2if import RP2040_u2if

# rst : 64 + 11 - 2 = 73
# boot : 64 + 10 - 2 = 72
RST = 73
BOOT = 72

def init_rp2040() -> RP2040_u2if:
    rp2040 = RP2040_u2if()
    rp2040.open()

    rp2040.gpio_init_pin(RST, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)
    rp2040.gpio_init_pin(BOOT, RP2040_u2if.GPIO_OUT, RP2040_u2if.GPIO_PULL_NONE)

    return rp2040

def bootloader_mode(mode: int, rp2040: RP2040_u2if):
    rp2040.gpio_set_pin(BOOT, mode);
    time.sleep(0.05);
    rp2040.gpio_set_pin(RST, 0);
    time.sleep(0.2);
    rp2040.gpio_set_pin(RST, 1);
    time.sleep(0.05);

if __name__ == "__main__":
    if len(argv) < 2:
        print("Usage: set_prog_state.py <0|1>")
        exit(1)
    mode = int(argv[1])
    if mode not in (0, 1):
        print("Usage: set_prog_state.py <0|1>")
        exit(1)
    rp2040 = init_rp2040()
    if mode == 0:
        print("Setting unprogrammed state")
        bootloader_mode(1, rp2040)
    else:
        print("Setting programmed state")
        bootloader_mode(0, rp2040)