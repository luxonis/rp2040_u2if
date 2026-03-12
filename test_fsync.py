from rp2040_u2if import RP2040_u2if
import struct
import time
import argparse

# Helper functions

I2C_BUS = 0
I2C_CLK_SPEED = 400000
FSYNC_CONTROLLER_ADDR = 0x12

FSYNC_CONTROLLER_DATA_ENDIAN = '<' # little

def fsync_stm_bin(cmd: int, n: int) -> bytes:
    if n == 1:
        return struct.pack(FSYNC_CONTROLLER_DATA_ENDIAN + 'B', cmd)
    elif n == 2:
        return struct.pack(FSYNC_CONTROLLER_DATA_ENDIAN + 'H', cmd)
    elif n == 4:
        return struct.pack(FSYNC_CONTROLLER_DATA_ENDIAN + 'I', cmd)
    else:
        raise ValueError("Invalid number of bytes")
    # return cmd.to_bytes(n, byteorder=FSYNC_CONTROLLER_DATA_ENDIAN)

FSYNC_STM_FW_VERSION_REG = fsync_stm_bin(0x00, 1)
FSYNC_STM_UNLOCK_MAGIC = fsync_stm_bin(42, 1)

FSYNC_STM_CONFIG_REG = fsync_stm_bin(0x01, 1)
FSYNC_STM_CONFIG_REG_MASTER_INPUT = fsync_stm_bin(0x00, 4)
FSYNC_STM_CONFIG_REG_MASTER_OUTPUT = fsync_stm_bin(0x01, 4)
FSYNC_STM_CONFIG_REG_SLAVE_INPUT = fsync_stm_bin(0x02, 4)

FSYNC_STM_INTERNAL_FREQUENCY_REG = fsync_stm_bin(0x02, 1)
FSYNC_STM_ACTUAL_FREQUENCY_REG = fsync_stm_bin(0x03, 1)

FSYNC_STM_IN_PRESENT_REG = fsync_stm_bin(0x04, 1)
FSYNC_STM_IN_FREQ_REG = fsync_stm_bin(0x05, 1)
FSYNC_STM_IN_DUTY_REG = fsync_stm_bin(0x06, 1)

FSYNC_STM_OUTPUT_3_DUTY_CYCLE = fsync_stm_bin(0x0E, 1)
FSYNC_STM_OUTPUT_3_ACTIVE_LVL = fsync_stm_bin(0x0F, 1)

FSYNC_STM_OUTPUT_11_DUTY_CYCLE = fsync_stm_bin(0x1E, 1)
FSYNC_STM_OUTPUT_11_ACTIVE_LVL = fsync_stm_bin(0x1F, 1)

def fsync_stm_output_duty_cycle(duty_cycle: float) -> bytes:
    if duty_cycle < 0.0 or duty_cycle > 100.0:
        raise ValueError("Duty cycle must be between 0% and 100%")
    
    scale = 2048
    duty = int(round(duty_cycle / 100.0 * scale))
    duty = min(max(duty, 0), scale)

    return fsync_stm_bin(duty, 4)

def fsync_stm_internal_frequency(freq: float) -> bytes:
    if freq < 0.0 or freq > 600.0:
        raise ValueError("Frequency must be between 0Hz and 600Hz")
    
    return struct.pack(FSYNC_CONTROLLER_DATA_ENDIAN + 'f', freq)

FSYNC_STM_OUTPUT_ACTIVE_LVL_LOW = fsync_stm_bin(0x00, 4)
FSYNC_STM_OUTPUT_ACTIVE_LVL_HIGH = fsync_stm_bin(0x01, 4)

def fsync_stm_write(dev: RP2040_u2if, cmd: bytes) -> None:
    dev.i2c_writeto(FSYNC_CONTROLLER_ADDR, cmd)

def fsync_stm_read(dev: RP2040_u2if, cmd: bytes) -> bytes:
    resp = bytearray(4)
    dev.i2c_writeto_then_readfrom(FSYNC_CONTROLLER_ADDR, cmd, resp)
    return resp

def to_int(resp: bytes) -> int:
    if len(resp) == 1:
        return struct.unpack(FSYNC_CONTROLLER_DATA_ENDIAN + 'B', resp)[0]
    elif len(resp) == 2:
        return struct.unpack(FSYNC_CONTROLLER_DATA_ENDIAN + 'H', resp)[0]
    elif len(resp) == 4:
        return struct.unpack(FSYNC_CONTROLLER_DATA_ENDIAN + 'I', resp)[0]
    else:
        raise ValueError("Invalid number of bytes")
    # return int.from_bytes(resp, byteorder=FSYNC_CONTROLLER_DATA_ENDIAN)

def to_float(resp: bytes) -> float:
    if len(resp) == 4:
        return struct.unpack(FSYNC_CONTROLLER_DATA_ENDIAN + 'f', resp)[0]
    else:
        raise ValueError("Invalid number of bytes")

# End of helper functions


parser = argparse.ArgumentParser(description='FSYNC Controller Example')
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument('-s', '--slave', action='store_true', help='Slave mode')
group.add_argument('-m', '--master', action='store_true', help='Master mode')
args = parser.parse_args()

dev = RP2040_u2if()
dev.open()
dev.i2c_set_port(I2C_BUS)
dev.i2c_configure(I2C_CLK_SPEED)
slaves = dev.i2c_scan()

if FSYNC_CONTROLLER_ADDR not in slaves:
    print("FSYNC Controller not found")
    exit(1)

print("FSYNC Controller found")

#read fw version

def do_master_mode(dev: RP2040_u2if):
    # go to master mode
    fsync_stm_write(dev, FSYNC_STM_CONFIG_REG + FSYNC_STM_CONFIG_REG_MASTER_OUTPUT)

    # assert master mode
    mode = to_int(fsync_stm_read(dev, FSYNC_STM_CONFIG_REG))
    if mode != 1:
        print("Master mode not asserted, trying to unlock..")
        fsync_stm_write(dev, FSYNC_STM_FW_VERSION_REG + FSYNC_STM_UNLOCK_MAGIC)
        fsync_stm_write(dev, FSYNC_STM_CONFIG_REG + FSYNC_STM_CONFIG_REG_MASTER_OUTPUT)

        mode = to_int(fsync_stm_read(dev, FSYNC_STM_CONFIG_REG))
        if mode != 1:
            print("Master mode not asserted")
            exit(1)
    
    # enable output 11
    fsync_stm_write(dev, FSYNC_STM_OUTPUT_11_ACTIVE_LVL + FSYNC_STM_OUTPUT_ACTIVE_LVL_LOW)
    fsync_stm_write(dev, FSYNC_STM_OUTPUT_11_DUTY_CYCLE + fsync_stm_output_duty_cycle(50))
    fsync_stm_write(dev, FSYNC_STM_INTERNAL_FREQUENCY_REG + fsync_stm_internal_frequency(23.0))

    actual_frq = to_float(fsync_stm_read(dev, FSYNC_STM_ACTUAL_FREQUENCY_REG))
    print(f"Actual frequency: {actual_frq}")


def do_slave_mode(dev: RP2040_u2if):
    # go to slave mode
    fsync_stm_write(dev, FSYNC_STM_CONFIG_REG + FSYNC_STM_CONFIG_REG_SLAVE_INPUT)

    # assert slave mode
    mode = to_int(fsync_stm_read(dev, FSYNC_STM_CONFIG_REG))
    if mode != 2:
        print("Slave mode not asserted, trying to unlock..")
        fsync_stm_write(dev, FSYNC_STM_FW_VERSION_REG + FSYNC_STM_UNLOCK_MAGIC)
        fsync_stm_write(dev, FSYNC_STM_CONFIG_REG + FSYNC_STM_CONFIG_REG_SLAVE_INPUT)

        mode = to_int(fsync_stm_read(dev, FSYNC_STM_CONFIG_REG))
        if mode != 2:
            print("Slave mode not asserted")
            exit(1)

    # enable output 3
    fsync_stm_write(dev, FSYNC_STM_OUTPUT_3_ACTIVE_LVL + FSYNC_STM_OUTPUT_ACTIVE_LVL_LOW)
    fsync_stm_write(dev, FSYNC_STM_OUTPUT_3_DUTY_CYCLE + fsync_stm_output_duty_cycle(50))

    active_lvl = to_int(fsync_stm_read(dev, FSYNC_STM_OUTPUT_3_ACTIVE_LVL))
    duty = to_float(fsync_stm_read(dev, FSYNC_STM_OUTPUT_3_DUTY_CYCLE))

    print(f"Active level: {active_lvl}")
    print(f"Duty cycle: {100.0*duty/2048.0}")

    while True:
        in_present = to_int(fsync_stm_read(dev, FSYNC_STM_IN_PRESENT_REG))
        in_freq = to_float(fsync_stm_read(dev, FSYNC_STM_IN_FREQ_REG))
        in_duty = to_float(fsync_stm_read(dev, FSYNC_STM_IN_DUTY_REG))

        print("INPUT")
        print(f"\tInput present: {in_present}")
        print(f"\tInput frequency: {in_freq}")
        print(f"\tInput duty: {in_duty}")
        time.sleep(1)


fw_ver = to_int(fsync_stm_read(dev, FSYNC_STM_FW_VERSION_REG))
print("FW Version: %d" % fw_ver)
if fw_ver != 12:
    print("FW Version not supported")
    exit(1)


if args.slave:
    do_slave_mode(dev)
elif args.master:
    do_master_mode(dev)
else:
    print("No mode specified")
    exit(1)
