# SPDX-FileCopyrightText: 2021 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""Helper class for use with RP2040 running u2if firmware"""
# https://github.com/execuc/u2if

import os
import time
import hid

# Use to set delay between reset and device reopen. if negative, don't reset at all
RP2040_U2IF_RESET_DELAY = float(os.environ.get("RP2040_U2IF_RESET_DELAY", 1))

# pylint: disable=import-outside-toplevel,too-many-branches,too-many-statements
# pylint: disable=too-many-arguments,too-many-function-args, too-many-public-methods


class RP2040_u2if:
    """Helper class for use with RP2040 running u2if firmware"""

    # MISC
    RESP_OK = 0x01
    RESP_NOK = 0x02
    RESP_NOT_CONCERNED = 0xFF

    SYS_RESET = 0x10

    # GPIO
    GPIO_INIT_PIN = 0x20
    GPIO_SET_VALUE = 0x21
    GPIO_GET_VALUE = 0x22
    # Values
    GPIO_IN = 0
    GPIO_OUT = 1
    GPIO_LOW = 0
    GPIO_HIGH = 1
    GPIO_PULL_NONE = 0
    GPIO_PULL_UP = 1
    GPIO_PULL_DOWN = 2

    # GPIO IRQ
    GPIO_SET_IRQ = 0x23
    GPIO_GET_IRQ = 0x24

    IRQ_EVENT_NONE = 0
    IRQ_EVENT_RISING = 1
    IRQ_EVENT_FALLING = 2

    # ADC
    ADC_INIT_PIN = 0x40
    ADC_GET_VALUE = 0x41

    # I2C
    I2C0_INIT = 0x80
    I2C0_DEINIT = 0x81
    I2C0_WRITE = 0x82
    I2C0_READ = 0x83
    I2C0_WRITE_FROM_UART = 0x84
    I2C1_INIT = I2C0_INIT + 0x10
    I2C1_DEINIT = I2C0_DEINIT + 0x10
    I2C1_WRITE = I2C0_WRITE + 0x10
    I2C1_READ = I2C0_READ + 0x10
    I2C1_WRITE_FROM_UART = I2C0_WRITE_FROM_UART + 0x10

    # SPI
    SPI0_INIT = 0x60
    SPI0_DEINIT = 0x61
    SPI0_WRITE = 0x62
    SPI0_READ = 0x63
    SPI0_WRITE_FROM_UART = 0x64
    SPI1_INIT = SPI0_INIT + 0x10
    SPI1_DEINIT = SPI0_DEINIT + 0x10
    SPI1_WRITE = SPI0_WRITE + 0x10
    SPI1_READ = SPI0_READ + 0x10
    SPI1_WRITE_FROM_UART = SPI0_WRITE_FROM_UART + 0x10

    # WS2812B (LED)
    WS2812B_INIT = 0xA0
    WS2812B_DEINIT = 0xA1
    WS2812B_WRITE = 0xA2

    # PWM
    PWM_INIT_PIN = 0x30
    PWM_DEINIT_PIN = 0x31
    PWM_SET_FREQ = 0x32
    PWM_GET_FREQ = 0x33
    PWM_SET_DUTY_U16 = 0x34
    PWM_GET_DUTY_U16 = 0x35
    PWM_SET_DUTY_NS = 0x36
    PWM_GET_DUTY_NS = 0x37

    # UART0
    UART0_INIT = 0x50
    UART0_DEINIT = 0x51
    UART0_WRITE = 0x52
    UART0_READ = 0x53

    # UART1
    UART0_UART1_OFFSET = 0x70
    UART1_INIT = UART0_INIT + UART0_UART1_OFFSET
    UART1_DEINIT = UART0_DEINIT + UART0_UART1_OFFSET
    UART1_WRITE = UART0_WRITE + UART0_UART1_OFFSET
    UART1_READ = UART0_READ + UART0_UART1_OFFSET

    # FSYNC CONTROLLER
    FSYNC_ADDRESS = 0x12
    FSYNC_BOOT_ADDRESS = 0x56

    FSYNC_RST_PIN = 64 + 14

    FSYNC_INIT = 0xE0
    FSYNC_PROBE = 0xE1
    FSYNC_GETPINCAPABILITIES = 0xE2
    FSYNC_SETPINCAPABILITIES = 0xE3
    FSYNC_GETMODE = 0xE4
    FSYNC_SETMODE = 0xE5
    FSYNC_GETFPS = 0xE6
    FSYNC_SETFPS = 0xE7
    FSYNC_GETDUTY = 0xE8
    FSYNC_SETDUTY = 0xE9
    FSYNC_GETPOLARITY = 0xEA
    FSYNC_SETPOLARITY = 0xEB
    FSYNC_GETINPUTINFO = 0xEC

    FSYNC_MODE_INPUT = 0
    FSYNC_MODE_MASTER = 1
    FSYNC_MODE_SLAVE = 2

    FSYNC_CHANNEL_PB1_ID = 0
    FSYNC_CHANNEL_PA4_ID = 1
    FSYNC_CHANNEL_PA1_ID = 2
    FSYNC_CHANNEL_PB0_ID = 3
    FSYNC_CHANNEL_PA8_ID = 4
    FSYNC_CHANNEL_PA5_ID = 5
    FSYNC_CHANNEL_PA6_ID = 6
    FSYNC_CHANNEL_PA7_ID = 7
    FSYNC_CHANNEL_PA3_ID = 8
    FSYNC_CHANNEL_PC6_ID = 9
    FSYNC_CHANNEL_PB8_ID = 10
    FSYNC_CHANNEL_PA11_ID = 11
    FSYNC_CHANNEL_PB5_ID = 12

    FSYNC_PIN_PA0_ID = 0
    FSYNC_PIN_PA1_ID = 1
    FSYNC_PIN_PA2_ID = 2
    FSYNC_PIN_PA3_ID = 3
    FSYNC_PIN_PA4_ID = 4
    FSYNC_PIN_PA5_ID = 5
    FSYNC_PIN_PA6_ID = 6
    FSYNC_PIN_PA7_ID = 7
    FSYNC_PIN_PA8_ID = 8
    FSYNC_PIN_PA11_ID = 9
    FSYNC_PIN_PA12_ID = 10
    FSYNC_PIN_PA13_ID = 11
    FSYNC_PIN_PA14_ID = 12
    FSYNC_PIN_PA15_ID = 13
    FSYNC_PIN_PB0_ID = 14
    FSYNC_PIN_PB1_ID = 15
    FSYNC_PIN_PB3_ID = 16
    FSYNC_PIN_PB4_ID = 17
    FSYNC_PIN_PB5_ID = 18
    FSYNC_PIN_PB8_ID = 19
    FSYNC_PIN_PC6_ID = 20
    
    FSYNC_PIN_CONFIG_TYPE_HIGH_Z = 1
    FSYNC_PIN_CONFIG_TYPE_PWM = 2
    FSYNC_PIN_CONFIG_TYPE_ADC = 4
    FSYNC_PIN_CONFIG_TYPE_PWM_KEEPAWAKE = 8
    FSYNC_PIN_CONFIG_TYPE_PWM_1200PAD = 16
    
    def __init__(self):
        self._vid = None
        self._pid = None
        self._hid = None
        self._opened = False
        self._i2c_index = None
        self._spi_index = None
        self._uart_index = None
        self._serial = None
        self._neopixel_initialized = False
        self._uart_rx_carry = [bytearray(), bytearray()]

    def _hid_xfer(self, report, response=True):
        """Perform HID Transfer"""
        # first byte is report ID, which =0
        # remaing bytes = 64 byte report data
        # https://github.com/libusb/hidapi/blob/083223e77952e1ef57e6b77796536a3359c1b2a3/hidapi/hidapi.h#L185
        self._hid.write(b"\0" + report + b"\0" * (64 - len(report)))
        if response:
            # return is 64 byte response report
            ret = self._hid.read(64, timeout_ms=1000) # Sometimes this can hang, but if we time out the call, it will work on the next call
            assert len(ret) == 64, "HID Timeout occurred."
            return ret
        return None

    def _reset(self):
        self._hid_xfer(bytes([self.SYS_RESET]), False)
        self._hid.close()
        time.sleep(RP2040_U2IF_RESET_DELAY)
        start = time.monotonic()
        while time.monotonic() - start < 5:
            try:
                self._hid.open(self._vid, self._pid, self._serial)
            except OSError:
                time.sleep(0.1)
                continue
            return
        raise OSError("RP2040 u2if open error.")

    # ----------------------------------------------------------------
    # MISC
    # ----------------------------------------------------------------
    def open(self, vid = 0xcafe, pid = 0x4005, serial = None):
        """Open HID interface for given USB VID and PID."""

        if self._opened:
            return
        self._vid = vid
        self._pid = pid
        self._serial = serial
        self._hid = hid.device()
        self._hid.open(self._vid, self._pid, self._serial)
        if RP2040_U2IF_RESET_DELAY >= 0:
            self._reset()

        # reset stm
        self.gpio_init_pin(
            self.FSYNC_RST_PIN, self.GPIO_OUT, self.GPIO_PULL_NONE
        )

        self.gpio_set_pin(self.FSYNC_RST_PIN, 0)
        time.sleep(0.1)
        self.gpio_set_pin(self.FSYNC_RST_PIN, 1)
        time.sleep(0.1)
        self.gpio_set_pin(self.FSYNC_RST_PIN, 0)

        """
        This is diabolical. For some unknown reason, the first query always fails.
        So we're basically just issuing a random query to get around this.
        """
        self._hid_xfer(
            bytes([self.FSYNC_GETPINCAPABILITIES, 3]),
            True,
        )

        self._opened = True

    def close(self):
        """Close HID interface."""
        if not self._opened:
            return

        # reset stm
        self.gpio_init_pin(
            self.FSYNC_RST_PIN, self.GPIO_OUT, self.GPIO_PULL_NONE
        )

        self.gpio_set_pin(self.FSYNC_RST_PIN, 0)
        time.sleep(0.1)
        self.gpio_set_pin(self.FSYNC_RST_PIN, 1)
        time.sleep(0.1)
        self.gpio_set_pin(self.FSYNC_RST_PIN, 0)

        self._hid_xfer(bytes([self.SYS_RESET]), True)
        self._hid.close()
        self._opened = False
    
    # ----------------------------------------------------------------
    # GPIO
    # ----------------------------------------------------------------
    def gpio_init_pin(self, pin_id, direction, pull):
        """Configure GPIO Pin."""
        self._hid_xfer(
            bytes(
                [
                    self.GPIO_INIT_PIN,
                    pin_id,
                    direction,
                    pull,
                ]
            )
        )

    def gpio_set_pin(self, pin_id, value):
        """Set Current GPIO Pin Value"""
        self._hid_xfer(
            bytes(
                [
                    self.GPIO_SET_VALUE,
                    pin_id,
                    int(value),
                ]
            )
        )

    def gpio_get_pin(self, pin_id):
        """Get Current GPIO Pin Value"""
        resp = self._hid_xfer(
            bytes(
                [
                    self.GPIO_GET_VALUE,
                    pin_id,
                ]
            ),
            True,
        )
        return resp[3] != 0x00
    
    def gpio_set_irq(self, pin_id, events, debounced=True):
        """
        Configure interrupt events for a GPIO pin.

        Parameters
        ----------
        pin_id : int
            GPIO number
        events : int
            IRQ_EVENT_RISING | IRQ_EVENT_FALLING
        debounced : bool
            Use firmware debouncing
        """

        self._hid_xfer(
            bytes([
                self.GPIO_SET_IRQ,
                pin_id,
                events,
                1 if debounced else 0
            ])
        )


    # ----------------------------------------------------------------
    # GPIO IRQ
    # ----------------------------------------------------------------

    def gpio_get_irq(self):
        """
        Retrieve GPIO interrupt events.
    
        Returns
        -------
        list[tuple]
            List of (gpio, event) tuples.
        """
    
        resp = self._hid_xfer(
            bytes([self.GPIO_GET_IRQ]),
            True,
        )
    
        if resp[1] != self.RESP_OK:
            return []
    
        irq_count = resp[2]
    
        events = []
    
        for i in range(irq_count):
        
            ev = resp[3 + i]
    
            gpio = ev & 0x3F
            event = (ev >> 6) & 0x03
    
            events.append((gpio, event))
    
        return events

    # ----------------------------------------------------------------
    # ADC
    # ----------------------------------------------------------------
    def adc_init_pin(self, pin_id):
        """Configure ADC Pin."""
        self._hid_xfer(
            bytes(
                [
                    self.ADC_INIT_PIN,
                    pin_id,
                ]
            )
        )

    def adc_get_value(self, pin_id):
        """Get ADC value for pin."""
        resp = self._hid_xfer(
            bytes(
                [
                    self.ADC_GET_VALUE,
                    pin_id,
                ]
            ),
            True,
        )
        return int.from_bytes(resp[3 : 3 + 2], byteorder="little")

    # ----------------------------------------------------------------
    # I2C
    # ----------------------------------------------------------------
    def i2c_configure(self, baudrate, sda, scl, pullup=False):
        """Configure I2C."""
        if self._i2c_index is None:
            raise RuntimeError("I2C bus not initialized.")

        if sda not in [0, 4, 8, 12, 16, 20, 24, 28]:
            raise RuntimeError("Invalid SDA pin")

        if scl not in [1, 5, 9, 13, 17, 21, 25, 29]:
            raise RuntimeError("Invalid SCL pin")

        resp = self._hid_xfer(
            bytes(
                [
                    self.I2C0_INIT if self._i2c_index == 0 else self.I2C1_INIT,
                    0x00 if not pullup else 0x01,
                ]
            )
            + baudrate.to_bytes(4, byteorder="little")
            + sda.to_bytes(4, byteorder="little")
            + scl.to_bytes(4, byteorder="little"),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("I2C init error.")

    def i2c_set_port(self, index):
        """Set I2C port."""
        if index not in (0, 1):
            raise ValueError("I2C index must be 0 or 1.")
        self._i2c_index = index

    def _i2c_write(self, address, buffer, start=0, end=None, stop=True):
        """Write data from the buffer to an address"""
        if self._i2c_index is None:
            raise RuntimeError("I2C bus not initialized.")

        end = end if end else len(buffer)

        write_cmd = self.I2C0_WRITE if self._i2c_index == 0 else self.I2C1_WRITE
        stop_flag = 0x01 if stop else 0x00

        while (end - start) > 0:
            remain_bytes = end - start
            chunk = min(remain_bytes, 64 - 7)
            resp = self._hid_xfer(
                bytes([write_cmd, address, stop_flag])
                + remain_bytes.to_bytes(4, byteorder="little")
                + buffer[start : (start + chunk)],
                True,
            )
            if resp[1] != self.RESP_OK:
                raise RuntimeError("I2C write error")
            start += chunk

    def _i2c_read(self, address, buffer, start=0, end=None):
        """Read data from an address and into the buffer"""
        # TODO: support chunkified reads
        if self._i2c_index is None:
            raise RuntimeError("I2C bus not initialized.")

        end = end if end else len(buffer)

        read_cmd = self.I2C0_READ if self._i2c_index == 0 else self.I2C1_READ
        stop_flag = 0x01  # always stop
        read_size = end - start

        resp = self._hid_xfer(bytes([read_cmd, address, stop_flag, read_size]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("I2C write error")
        # move into buffer
        for i in range(read_size):
            buffer[start + i] = resp[i + 2]

    def i2c_writeto(self, address, buffer, *, start=0, end=None):
        """Write data from the buffer to an address"""
        self._i2c_write(address, buffer, start, end)

    def i2c_readfrom_into(self, address, buffer, *, start=0, end=None):
        """Read data from an address and into the buffer"""
        self._i2c_read(address, buffer, start, end)

    def i2c_writeto_then_readfrom(
        self,
        address,
        out_buffer,
        in_buffer,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None,
    ):
        """Write data from buffer_out to an address and then
        read data from an address and into buffer_in
        """
        self._i2c_write(address, out_buffer, out_start, out_end, False)
        self._i2c_read(address, in_buffer, in_start, in_end)

    def i2c_scan(self, *, start=0, end=0x79):
        """Perform an I2C Device Scan"""
        if self._i2c_index is None:
            raise RuntimeError("I2C bus not initialized.")
        found = []
        for addr in range(start, end + 1):
            # try a write
            try:
                self.i2c_writeto(addr, b"\x00\x00\x00")
            except RuntimeError:  # no reply!
                continue
            # store if success
            found.append(addr)
        return found

    # ----------------------------------------------------------------
    # SPI
    # ----------------------------------------------------------------
    def spi_configure(self, baudrate):
        """Configure SPI."""
        if self._spi_index is None:
            raise RuntimeError("SPI bus not initialized.")

        resp = self._hid_xfer(
            bytes(
                [
                    self.SPI0_INIT if self._spi_index == 0 else self.SPI1_INIT,
                    0x00,  # mode, not yet implemented
                ]
            )
            + baudrate.to_bytes(4, byteorder="little"),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("SPI init error.")

    def spi_set_port(self, index):
        """Set SPI port."""
        if index not in (0, 1):
            raise ValueError("SPI index must be 0 or 1.")
        self._spi_index = index

    def spi_write(self, buffer, *, start=0, end=None):
        """SPI write."""
        if self._spi_index is None:
            raise RuntimeError("SPI bus not initialized.")

        end = end if end else len(buffer)

        write_cmd = self.SPI0_WRITE if self._spi_index == 0 else self.SPI1_WRITE

        while (end - start) > 0:
            remain_bytes = end - start
            chunk = min(remain_bytes, 64 - 3)
            resp = self._hid_xfer(
                bytes([write_cmd, chunk]) + buffer[start : (start + chunk)], True
            )
            if resp[1] != self.RESP_OK:
                raise RuntimeError("SPI write error")
            start += chunk

    def spi_readinto(self, buffer, *, start=0, end=None, write_value=0):
        """SPI readinto."""
        if self._spi_index is None:
            raise RuntimeError("SPI bus not initialized.")

        end = end if end else len(buffer)
        read_cmd = self.SPI0_READ if self._spi_index == 0 else self.SPI1_READ
        read_size = end - start

        resp = self._hid_xfer(bytes([read_cmd, write_value, read_size]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("SPI write error")
        # move into buffer
        for i in range(read_size):
            buffer[start + i] = resp[i + 2]

    def spi_write_readinto(
        self,
        buffer_out,
        buffer_in,
        *,
        out_start=0,
        out_end=None,
        in_start=0,
        in_end=None,
    ):
        """SPI write and readinto."""
        raise NotImplementedError("SPI write_readinto Not implemented")

    # ----------------------------------------------------------------
    # UART
    # ----------------------------------------------------------------
    def uart_init(self, index: int, baudrate: int = 9600, flush_rx: bool =True):
        """Initializes an UART port.
    
        Parameters
        ----------
        uart : int
            UART index (0 or 1)
        baudrate : int
            UART baud rate
        flush_rx : bool
            Whether to flush the RX buffer on initialization.    
        """
        self._validate_uart_index_T(index)
    
        uart_cmd = self.UART0_INIT if index == 0 else self.UART1_INIT
        resp = self._hid_xfer(
            bytes([uart_cmd, 0x00]) + baudrate.to_bytes(4, byteorder="little"),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("UART init error.")

        if flush_rx:
            self.uart_flush_rx(index)

    def uart_deinit(self, index: int):
        """Deinitializes an UART port."""
        self._validate_uart_index_T(index)

        uart_cmd = self.UART0_DEINIT if index == 0 else self.UART1_DEINIT
        resp = self._hid_xfer(bytes([uart_cmd]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("UART deinit error.")

    def _validate_uart_index_T(self, index: int):
        if index < 0 or index > 1:
            raise ValueError("UART index must be 0 or 1.")

    def _get_uart_read_cmd(self, index: int) -> int:
        return self.UART0_READ if index == 0 else self.UART1_READ
        
    def _uart_read_rx_buffer(self, uart_cmd: int):
        resp = self._hid_xfer(bytes([uart_cmd]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("UART read rx buffer error.")

        payload_size = resp[2]
        return bytes(resp[3:3 + payload_size])

    def uart_flush_rx(self, index: int, max_reads=32) -> int:
        """Clear pending UART RX bytes from host and firmware buffers."""
        self._validate_uart_index_T(index)


        uart_cmd = self._get_uart_read_cmd(index)
        flushed_bytes = len(self._uart_rx_carry[index])
        self._uart_rx_carry[index].clear()
        for _ in range(max_reads):
            chunk = self._uart_read_rx_buffer(uart_cmd)
            payload_size = len(chunk)
            if payload_size == 0:
                break
            flushed_bytes += payload_size

        return flushed_bytes

    def uart_read(self, index: int) -> bytes:
        """Read all currently available UART bytes."""
        self._validate_uart_index_T(index)

        data = bytearray(self._uart_rx_carry[index])
        uart_cmd = self._get_uart_read_cmd(index)
        self._uart_rx_carry[index].clear()

        while True:
            chunk = self._uart_read_rx_buffer(uart_cmd)
            
            if not chunk:
                break

            data.extend(chunk)

        return bytes(data)

    def uart_readline(self, index: int, timeout=None) -> bytes:
        """
        Reads from UART until newline is received.
        """
        self._validate_uart_index_T(index)

        UART_END_LINE_CHAR = 10
        uart_cmd = self._get_uart_read_cmd(index)
        carry = self._uart_rx_carry[index]

        start_time = time.time()
        while True:
            if UART_END_LINE_CHAR in carry:
                break

            chunk = self._uart_read_rx_buffer(uart_cmd)
            if chunk:
                carry.extend(chunk)

            if timeout is not None and (time.time() - start_time) > timeout:
                break

        if UART_END_LINE_CHAR not in carry:
            return b""

        end_idx = carry.index(UART_END_LINE_CHAR) + 1
        out = bytes(carry[:end_idx])
        del carry[:end_idx]
        
        return out

    def uart_write(self, index: int, data):
        """Write bytes to UART."""
        self._validate_uart_index_T(index)

        if isinstance(data, list):
            data = bytes(data)
    
        uart_cmd = self.UART0_WRITE if index == 0 else self.UART1_WRITE
    
        start = 0
        end = len(data)
    
        while (end - start) > 0:
            remain = end - start
            chunk = min(remain, 64 - 3)
    
            resp = self._hid_xfer(
                bytes([uart_cmd, chunk]) + data[start:start + chunk],
                True,
            )
    
            if resp[1] != self.RESP_OK:
                raise RuntimeError("UART write error")
    
            start += chunk

    # ----------------------------------------------------------------
    # NEOPIXEL
    # ----------------------------------------------------------------
    def neopixel_write(self, gpio, buf):
        """NeoPixel write."""
        # open serial (data is sent over this)
        if self._serial is None:
            import serial
            import serial.tools.list_ports

            ports = serial.tools.list_ports.comports()
            for port in ports:
                if port.vid == self._vid and port.pid == self._pid:
                    self._serial = serial.Serial(port.device)
                    break
        if self._serial is None:
            raise RuntimeError("Could not find Pico com port.")

        # init
        if not self._neopixel_initialized:
            # deinit any current setup
            # pylint: disable=protected-access
            self._hid_xfer(bytes([self.WS2812B_DEINIT]))
            resp = self._hid_xfer(
                bytes(
                    [
                        self.WS2812B_INIT,
                        gpio._pin.id,
                    ]
                ),
                True,
            )
            if resp[1] != self.RESP_OK:
                raise RuntimeError("Neopixel init error")
            self._neopixel_initialized = True

        self._serial.reset_output_buffer()

        # write
        # command is done over HID
        remain_bytes = len(buf)
        resp = self._hid_xfer(
            bytes([self.WS2812B_WRITE]) + remain_bytes.to_bytes(4, byteorder="little"),
            True,
        )
        if resp[1] != self.RESP_OK:
            # pylint: disable=no-else-raise
            if resp[2] == 0x01:
                raise RuntimeError(
                    "Neopixel write error : too many pixel for the firmware."
                )
            elif resp[2] == 0x02:
                raise RuntimeError(
                    "Neopixel write error : transfer already in progress."
                )
            else:
                raise RuntimeError("Neopixel write error.")
        # buffer is sent over serial
        self._serial.write(buf)
        # hack (see u2if)
        if len(buf) % 64 == 0:
            self._serial.write([0])
        self._serial.flush()
        # polling loop to wait for write complete?
        time.sleep(0.1)
        resp = self._hid.read(64)
        while resp[0] != self.WS2812B_WRITE:
            resp = self._hid.read(64)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("Neopixel write (flush) error.")

    # ----------------------------------------------------------------
    # PWM
    # ----------------------------------------------------------------
    # pylint: disable=unused-argument
    def pwm_configure(self, pin_id: int, frequency=500, duty_cycle=0, variable_frequency=False):
        """Configure PWM."""
        self.pwm_deinit(pin_id)
        resp = self._hid_xfer(bytes([self.PWM_INIT_PIN, pin_id]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("PWM init error.")

        self.pwm_set_frequency(pin_id, frequency)
        self.pwm_set_duty_cycle(pin_id, duty_cycle)

    def pwm_deinit(self, pin_id: int):
        """Deinit PWM."""
        self._hid_xfer(bytes([self.PWM_DEINIT_PIN, pin_id]))

    def pwm_get_frequency(self, pin_id: int):
        """PWM get freq."""
        resp = self._hid_xfer(bytes([self.PWM_GET_FREQ, pin_id]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("PWM get frequency error.")
        return int.from_bytes(resp[3 : 3 + 4], byteorder="little")

    def pwm_set_frequency(self, pin_id: int, frequency):
        """PWM set freq."""
        resp = self._hid_xfer(
            bytes([self.PWM_SET_FREQ, pin_id])
            + frequency.to_bytes(4, byteorder="little"),
            True,
        )
        if resp[1] != self.RESP_OK:
            # pylint: disable=no-else-raise
            if resp[3] == 0x01:
                raise RuntimeError("PWM different frequency on same slice.")
            elif resp[3] == 0x02:
                raise RuntimeError("PWM frequency too low.")
            elif resp[3] == 0x03:
                raise RuntimeError("PWM frequency too high.")
            else:
                raise RuntimeError("PWM frequency error.")

    def pwm_get_duty_cycle(self, pin_id: int):
        """PWM get duty cycle."""
        resp = self._hid_xfer(bytes([self.PWM_GET_DUTY_U16, pin_id]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("PWM get duty cycle error.")
        return int.from_bytes(resp[3 : 3 + 4], byteorder="little")

    def pwm_set_duty_cycle(self, pin_id: int, duty_cycle):
        """PWM set duty cycle."""
        resp = self._hid_xfer(
            bytes([self.PWM_SET_DUTY_U16, pin_id])
            + duty_cycle.to_bytes(2, byteorder="little"),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("PWM set duty cycle error.")
    
    # ----------------------------------------------------------------
    # FSYNC CONTROLLER
    # ----------------------------------------------------------------
    def fsync_init(self):
        """Initialize the FSYNC controller."""
        resp = self._hid_xfer(bytes([self.FSYNC_INIT]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC init error.")

    def fsync_probe(self):
        """
        Probe for the FSYNC controller.

        Returns
        -------
        tuple
            (i2c_bus, address, firmware_version)
        """
        resp = self._hid_xfer(bytes([self.FSYNC_PROBE]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC controller not found.")

        i2c_bus = resp[2]
        address = resp[3]
        firmware_version = int.from_bytes(
            resp[4:8], byteorder="little", signed=False
        )

        return i2c_bus, address, firmware_version

    def fsync_get_pin_capabilities(self, pin):
        """Get FSYNC pin capability."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_GETPINCAPABILITIES, pin]),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC get pin capabilities error.")

        return int.from_bytes(
            resp[2:6], byteorder="little", signed=False
        )

    def fsync_set_pin_capabilities(self, pin, capability):
        """Set FSYNC pin capability."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_SETPINCAPABILITIES, pin])
            + int(capability).to_bytes(4, byteorder="little", signed=False),
            True,
        )

        if resp[1] != self.RESP_OK:
            error = resp[2]

            if error == 1:
                raise RuntimeError("FSYNC pin capability I2C error.")
            if error == 2:
                raise RuntimeError("FSYNC controller already initialized.")
            if error == 3:
                raise ValueError("Invalid FSYNC pin or capability.")

            raise RuntimeError("FSYNC set pin capabilities error.")

    def fsync_get_mode(self):
        """Get FSYNC controller mode."""
        resp = self._hid_xfer(bytes([self.FSYNC_GETMODE]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC get mode error.")

        return int.from_bytes(
            resp[2:6], byteorder="little", signed=False
        )

    def fsync_set_mode(self, mode):
        """Set FSYNC controller mode."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_SETMODE])
            + int(mode).to_bytes(4, byteorder="little", signed=False),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC set mode error.")

    def fsync_get_fps(self):
        """
        Get FSYNC frequencies.

        Returns
        -------
        tuple
            (requested_fps, actual_fps)
        """
        import struct

        resp = self._hid_xfer(bytes([self.FSYNC_GETFPS]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC get FPS error.")

        requested_fps = struct.unpack("<f", bytes(resp[2:6]))[0]
        actual_fps = struct.unpack("<f", bytes(resp[6:10]))[0]

        return requested_fps, actual_fps

    def fsync_set_fps(self, fps):
        """Set FSYNC output frequency in frames per second."""
        import struct

        resp = self._hid_xfer(
            bytes([self.FSYNC_SETFPS]) + struct.pack("<f", float(fps)),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC set FPS error.")

    def fsync_get_duty(self, channel):
        """Get FSYNC channel duty value."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_GETDUTY, channel]),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC get duty error.")

        return int.from_bytes(
            resp[2:6], byteorder="little", signed=False
        )

    def fsync_set_duty(self, channel, duty):
        """Set FSYNC channel duty value."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_SETDUTY, channel])
            + int(duty).to_bytes(4, byteorder="little", signed=False),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC set duty error.")

    def fsync_get_polarity(self, channel):
        """Get FSYNC channel polarity."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_GETPOLARITY, channel]),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC get polarity error.")

        return int.from_bytes(
            resp[2:6], byteorder="little", signed=False
        )

    def fsync_set_polarity(self, channel, polarity):
        """Set FSYNC channel polarity."""
        resp = self._hid_xfer(
            bytes([self.FSYNC_SETPOLARITY, channel])
            + int(polarity).to_bytes(4, byteorder="little", signed=False),
            True,
        )
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC set polarity error.")

    def fsync_get_input_info(self):
        """
        Get FSYNC input information.

        Returns
        -------
        tuple
            (present, fps, duty)
        """
        import struct

        resp = self._hid_xfer(bytes([self.FSYNC_GETINPUTINFO]), True)
        if resp[1] != self.RESP_OK:
            raise RuntimeError("FSYNC get input info error.")

        present = bool(resp[2])
        fps = struct.unpack("<f", bytes(resp[3:7]))[0]
        duty = int.from_bytes(
            resp[7:11], byteorder="little", signed=False
        )

        return present, fps, duty

