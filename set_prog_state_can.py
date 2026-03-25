import time
from sys import argv
from src.luxonis_u2if.controller_box import ControllerBox

# rst : 64 + 11 - 2 = 73
# boot : 64 + 10 - 2 = 72
RST = 73
BOOT = 72

def init() -> ControllerBox:
    controller_box = ControllerBox()

    controller_box.gpio_init(RST, ControllerBox.GPIO_OUT, ControllerBox.GPIO_PULL_NONE)
    controller_box.gpio_init(BOOT, ControllerBox.GPIO_OUT, ControllerBox.GPIO_PULL_NONE)

    return controller_box

def bootloader_mode(mode: int, controller_box: ControllerBox):
    controller_box.gpio_set(BOOT, mode);
    time.sleep(0.05);
    controller_box.gpio_set(RST, 0);
    time.sleep(0.2);
    controller_box.gpio_set(RST, 1);
    time.sleep(0.05);

if __name__ == "__main__":
    if len(argv) < 2:
        print("Usage: set_prog_state.py <0|1>")
        exit(1)
    mode = int(argv[1])
    if mode not in (0, 1):
        print("Usage: set_prog_state.py <0|1>")
        exit(1)
    controller_box = init()
    if mode == 0:
        print("Setting unprogrammed state")
        bootloader_mode(1, controller_box)
    else:
        print("Setting programmed state")
        bootloader_mode(0, controller_box)