from rp2040_u2if import RP2040_u2if
import time


dev = RP2040_u2if()
dev.open()
dev.fsync_controller_init()

out = RP2040_u2if.FsyncOutput.M8_FSYNC
dev.fsync_controller_set_mode(RP2040_u2if.FsyncMode.MASTER_OUTPUT)
dev.fsync_controller_set_frequency(0.1)
dev.fsync_controller_set_polarity(False, out)
dev.fsync_controller_set_duty_cycle(50.0, out)

frqs = [10, 20, 40]

for frq in frqs:
    actual_frq = dev.fsync_controller_set_frequency(frq)
    print(f"Set frequency to {frq} Hz, actual frequency is {actual_frq} Hz")
    time.sleep(1)

duty_cycles = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]

for duty_cycle in duty_cycles:
    actual_duty_cycle = dev.fsync_controller_set_duty_cycle(duty_cycle, out)
    print(f"Set duty cycle to {duty_cycle}%, actual duty cycle is {actual_duty_cycle}%")
    time.sleep(1)