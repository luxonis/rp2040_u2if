import time
import threading
import struct
from enum import Enum
from .rp2040_u2if import RP2040_u2if


class ControllerBox:
    """
    Hardware abstraction layer for the Controller Box.

    This class wraps the RP2040_u2if interface and provides a simple,
    board-oriented API for interacting with the Controller Box hardware.
    It handles logical GPIO remapping and exposes helper functions for
    controlling relays, LEDs, and reading buttons.
    """

    # Mapping GPIO
    GPIO_MAP = {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
        5: 4,
        6: 5,
        7: 6,
        8: 7,
        9: 8,
        10: 9,
        11: 10,
        12: 11,
        13: 12,
        14: 13,
        15: 26,
        16: 27,
    }

    REV_GPIO_MAP = {v: k for k, v in GPIO_MAP.items()}

    GPIO_IN = 0
    GPIO_OUT = 1
    GPIO_PULL_NONE = 0
    GPIO_PULL_UP = 1
    GPIO_PULL_DOWN = 2

    # IRQ event types
    IRQ_RISING = 1
    IRQ_FALLING = 2

    # Relays
    RELAY_PINS = {
        1: (64, 65),
        2: (66, 67),
        3: (68, 69),
        4: (70, 71),
    }

    RELAY_PULSE = 0.02

    # LEDs and Buttons
    LED_PINS = [17, 16, 18]
    BUTTON_PINS = [19, 20, 21]

    # ----------------------------------------------------------------
    # FSYNC CONTROLLER
    # ----------------------------------------------------------------

    FSYNC_I2C_BUS = 0
    FSYNC_I2C_CLK_SPEED = 400000
    FSYNC_CONTROLLER_ADDR = 0x12
    FSYNC_CONTROLLER_DATA_ENDIAN = "<"

    class FsyncMode(Enum):
        MASTER_INPUT = 0
        MASTER_OUTPUT = 1
        SLAVE = 2

    class FsyncOutput(Enum):
        ISOLATED_STROBE = 0
        M8_FSYNC = 1

    def __init__(self):
        """
        Initialize ControllerBox device.
        """

        self.rp2040 = RP2040_u2if()
        self.rp2040.open()

        self._btn_callback = None
        self._btn_thread = None
        self._running = False

    def close(self):
        self._running = False
        if self._btn_thread:
            self._btn_thread.join(timeout=0.1)
        self.rp2040.close()

    # ----------------------------------------------------------------
    # FSYNC helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _fsync_stm_bin(cmd: int, n: int) -> bytes:
        if n == 1:
            return struct.pack(ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "B", cmd)
        elif n == 2:
            return struct.pack(ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "H", cmd)
        elif n == 4:
            return struct.pack(ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "I", cmd)
        else:
            raise ValueError("Invalid number of bytes")

    @staticmethod
    def _fsync_stm_output_duty_cycle(duty_cycle: float) -> bytes:
        if duty_cycle < 0.0 or duty_cycle > 100.0:
            raise ValueError("Duty cycle must be between 0% and 100%")

        scale = 2048
        duty = int(round(duty_cycle / 100.0 * scale))
        duty = min(max(duty, 0), scale)

        return ControllerBox._fsync_stm_bin(duty, 4)

    @staticmethod
    def _fsync_stm_internal_frequency(freq: float) -> bytes:
        if freq < 0.0 or freq > 600.0:
            raise ValueError("Frequency must be between 0Hz and 600Hz")

        return struct.pack(ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "f", freq)

    def _fsync_stm_write(self, cmd: bytes) -> None:
        self.rp2040.i2c_writeto(self.FSYNC_CONTROLLER_ADDR, cmd)

    def _fsync_stm_read(self, cmd: bytes) -> bytes:
        resp = bytearray(4)
        self.rp2040.i2c_writeto_then_readfrom(self.FSYNC_CONTROLLER_ADDR, cmd, resp)
        return resp

    @staticmethod
    def _fsync_stm_to_int(resp: bytes) -> int:
        if len(resp) == 1:
            return struct.unpack(
                ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "B", resp
            )[0]
        elif len(resp) == 2:
            return struct.unpack(
                ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "H", resp
            )[0]
        elif len(resp) == 4:
            return struct.unpack(
                ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "I", resp
            )[0]
        else:
            raise ValueError("Invalid number of bytes")

    @staticmethod
    def _fsync_stm_to_float(resp: bytes) -> float:
        if len(resp) == 4:
            return struct.unpack(
                ControllerBox.FSYNC_CONTROLLER_DATA_ENDIAN + "f", resp
            )[0]
        else:
            raise ValueError("Invalid number of bytes")

    # ----------------------------------------------------------------
    # GPIO
    # ----------------------------------------------------------------

    def map_gpio(self, pin):
        """Translate logical GPIO to RP2040 physical pin."""
        return self.GPIO_MAP.get(pin, pin)

    def gpio_init(self, pin, direction, pull):
        """Initialize a GPIO using logical pin numbers."""
        gpio = self.map_gpio(pin)
        self.rp2040.gpio_init_pin(gpio, direction, pull)

    def gpio_set(self, pin, value):
        """Set a GPIO output value using logical pin numbers."""
        gpio = self.map_gpio(pin)
        self.rp2040.gpio_set_pin(gpio, int(value))

    def gpio_get(self, pin):
        """Read a GPIO value using logical pin numbers."""
        gpio = self.map_gpio(pin)
        return self.rp2040.gpio_get_pin(gpio)

    def gpio_set_irq(self, pin, event, debounce=True):
        """Configure GPIO interrupt using logical pin numbers."""
        gpio = self.map_gpio(pin)
        self.rp2040.gpio_set_irq(gpio, event, debounce)

    def gpio_get_irq(self):
        """
        Retrieve GPIO interrupt events using logical pin numbers.

        Returns
        -------
        list[(pin, event)]
        """
        events = self.rp2040.gpio_get_irq()

        return [(self.REV_GPIO_MAP.get(gpio, gpio), event) for gpio, event in events]

    # ----------------------------------------------------------------
    # OPTIONAL HELPERS
    # ----------------------------------------------------------------

    def init_all_mapped(self, direction, pull):
        """
        Initialize all GPIOs defined in GPIO_MAP.
        """
        for logical_pin in self.GPIO_MAP:
            self.gpio_init(logical_pin, direction, pull)

    # ----------------------------------------------------------------
    # RELAYS
    # ----------------------------------------------------------------

    def relay_init(self):
        """Initialize all relay GPIO pins."""
        for pinA, pinB in self.RELAY_PINS.values():

            self.rp2040.gpio_init_pin(
                pinA, self.rp2040.GPIO_OUT, self.rp2040.GPIO_PULL_NONE
            )

            self.rp2040.gpio_init_pin(
                pinB, self.rp2040.GPIO_OUT, self.rp2040.GPIO_PULL_NONE
            )

            self.rp2040.gpio_set_pin(pinA, 0)
            self.rp2040.gpio_set_pin(pinB, 0)

    def relay_set(self, relay: int):
        """Set relay (1..4)."""
        if relay not in self.RELAY_PINS:
            raise ValueError("Relay must be 1..4")

        pinA, pinB = self.RELAY_PINS[relay]

        self.rp2040.gpio_set_pin(pinA, 1)
        self.rp2040.gpio_set_pin(pinB, 0)

        time.sleep(self.RELAY_PULSE)

        self.rp2040.gpio_set_pin(pinA, 0)
        self.rp2040.gpio_set_pin(pinB, 0)

    def relay_reset(self, relay: int):
        """Reset relay (1..4)."""
        if relay not in self.RELAY_PINS:
            raise ValueError("Relay must be 1..4")

        pinA, pinB = self.RELAY_PINS[relay]

        self.rp2040.gpio_set_pin(pinA, 0)
        self.rp2040.gpio_set_pin(pinB, 1)

        time.sleep(self.RELAY_PULSE)

        self.rp2040.gpio_set_pin(pinA, 0)
        self.rp2040.gpio_set_pin(pinB, 0)

    # ----------------------------------------------------------------
    # BUTTON EVENTS
    # ----------------------------------------------------------------

    def set_btn_callback(self, callback):

        self._btn_callback = callback

        # Precompute GPIO → button index
        self._btn_map = {pin: i + 1 for i, pin in enumerate(self.BUTTON_PINS)}

        for pin in self.BUTTON_PINS:

            self.rp2040.gpio_init_pin(
                pin, self.rp2040.GPIO_IN, self.rp2040.GPIO_PULL_NONE
            )

            self.rp2040.gpio_set_irq(
                pin, self.rp2040.IRQ_EVENT_RISING | self.rp2040.IRQ_EVENT_FALLING, True
            )

        self._running = True

        self._btn_thread = threading.Thread(target=self._button_event_loop, daemon=True)

        self._btn_thread.start()

    def _button_event_loop(self):

        while self._running:

            for gpio, event in self.rp2040.gpio_get_irq():

                btn = self._btn_map.get(gpio)

                if btn is None:
                    continue

                # debug:
                # print("GPIO:", gpio, "BTN:", btn, "EVENT:", event)

                if event == self.rp2040.IRQ_EVENT_RISING:
                    state = True

                elif event == self.rp2040.IRQ_EVENT_FALLING:
                    state = False

                else:
                    continue

                if self._btn_callback:
                    self._btn_callback(btn, state)

            time.sleep(0.001)

    # ------------------------------------------------------------
    # LED CONTROL
    # ------------------------------------------------------------

    def led_init(self):
        """Initialize LEDs."""
        for pin in self.LED_PINS:
            self.rp2040.gpio_init_pin(
                pin, self.rp2040.GPIO_OUT, self.rp2040.GPIO_PULL_NONE
            )
            self.rp2040.gpio_set_pin(pin, 0)  # start OFF

    def led_on(self, index):
        """Turn LED on."""
        self.rp2040.gpio_set_pin(self.LED_PINS[index - 1], 1)

    def led_off(self, index):
        """Turn LED off."""
        self.rp2040.gpio_set_pin(self.LED_PINS[index - 1], 0)

    def led_set(self, index, state):
        """Set LED state."""
        self.rp2040.gpio_set_pin(self.LED_PINS[index - 1], int(state))

    # ----------------------------------------------------------------
    # SERIAL (UART1)
    # ----------------------------------------------------------------

    def serial_init(self, baudrate=9600):
        """
        Initialize the serial interface.

        Parameters
        ----------
        baudrate : int
            Communication speed in bits per second.
        """
        self.rp2040.uart_init(1, baudrate)

    def serial_write(self, data):
        """
        Send data over the serial interface.

        Parameters
        ----------
        data : bytes | str
            Data to send.
        """
        if isinstance(data, str):
            data = data.encode()

        self.rp2040.uart_write(1, data)

    def serial_read(self):
        """
        Read all available data from the serial interface.

        Returns
        -------
        bytes
            Data received.
        """
        return self.rp2040.uart_read(1)

    # ----------------------------------------------------------------
    # FSYNC
    # ----------------------------------------------------------------

    def fsync_controller_init(self):

        self.rp2040.i2c_set_port(self.FSYNC_I2C_BUS)
        self.rp2040.i2c_configure(self.FSYNC_I2C_CLK_SPEED)

        slaves = self.rp2040.i2c_scan(
            start=self.FSYNC_CONTROLLER_ADDR, end=self.FSYNC_CONTROLLER_ADDR + 1
        )

        if self.FSYNC_CONTROLLER_ADDR not in slaves:
            raise RuntimeError("FSYNC Controller not found")

        self._fsync_stm_write(
            self.FSYNC_STM_CONFIG_REG + self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT
        )

        mode = self._fsync_stm_read(self.FSYNC_STM_CONFIG_REG)

        if mode != self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT:

            self._fsync_stm_write(
                self.FSYNC_STM_FW_VERSION_REG + self.FSYNC_STM_UNLOCK_MAGIC
            )
            self._fsync_stm_write(
                self.FSYNC_STM_CONFIG_REG + self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT
            )

            mode = self._fsync_stm_read(self.FSYNC_STM_CONFIG_REG)

            if mode != self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT:
                raise RuntimeError("Unable to unlock FSYNC Controller")

        self._fsync_stm_write(
            self.FSYNC_STM_CONFIG_REG + self.FSYNC_STM_CONFIG_REG_MASTER_INPUT
        )

    def fsync_controller_set_mode(self, mode: FsyncMode):

        if mode == self.FsyncMode.MASTER_INPUT:
            mode_to_set = self.FSYNC_STM_CONFIG_REG_MASTER_INPUT
        elif mode == self.FsyncMode.MASTER_OUTPUT:
            mode_to_set = self.FSYNC_STM_CONFIG_REG_MASTER_OUTPUT
        elif mode == self.FsyncMode.SLAVE:
            mode_to_set = self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT
        else:
            raise ValueError("Invalid FsyncMode")

        self._fsync_stm_write(self.FSYNC_STM_CONFIG_REG + mode_to_set)

        read_mode = self._fsync_stm_read(self.FSYNC_STM_CONFIG_REG)

        if read_mode != mode_to_set:
            raise RuntimeError("Failed to set FsyncMode")

    def fsync_controller_set_frequency(self, freq: float) -> float:

        self._fsync_stm_write(
            self.FSYNC_STM_INTERNAL_FREQUENCY_REG
            + self._fsync_stm_internal_frequency(freq)
        )

        actual_frq = self._fsync_stm_read(self.FSYNC_STM_ACTUAL_FREQUENCY_REG)

        return self._fsync_stm_to_float(actual_frq)

    def fsync_controller_set_duty_cycle(
        self, duty_cycle: float, output: FsyncOutput
    ) -> float:

        if output == self.FsyncOutput.ISOLATED_STROBE:
            output_to_set = self.FSYNC_STM_OUTPUT_3_DUTY_CYCLE
        elif output == self.FsyncOutput.M8_FSYNC:
            output_to_set = self.FSYNC_STM_OUTPUT_11_DUTY_CYCLE
        else:
            raise ValueError("Invalid FsyncOutput")

        duty_cycle_to_set = self._fsync_stm_output_duty_cycle(duty_cycle)

        self._fsync_stm_write(output_to_set + duty_cycle_to_set)

        actual = self._fsync_stm_to_int(self._fsync_stm_read(output_to_set))

        return 100.0 * actual / 2048.0

    def fsync_controller_set_polarity(self, polarity: bool, output: FsyncOutput):

        if output == self.FsyncOutput.ISOLATED_STROBE:
            output_to_set = self.FSYNC_STM_OUTPUT_3_ACTIVE_LVL
        elif output == self.FsyncOutput.M8_FSYNC:
            output_to_set = self.FSYNC_STM_OUTPUT_11_ACTIVE_LVL
        else:
            raise ValueError("Invalid FsyncOutput")

        polarity_to_set = (
            self.FSYNC_STM_OUTPUT_ACTIVE_LVL_HIGH
            if polarity
            else self.FSYNC_STM_OUTPUT_ACTIVE_LVL_LOW
        )

        self._fsync_stm_write(output_to_set + polarity_to_set)

    def fsync_controller_input_detected(self) -> bool:

        present = self._fsync_stm_to_int(
            self._fsync_stm_read(self.FSYNC_STM_IN_PRESENT_REG)
        )

        if present == 0:
            return False
        elif present == 1:
            return True
        else:
            raise RuntimeError(f"Unexpected input present value: {present}")

    def fsync_controller_input_frequency(self) -> float:
        return self._fsync_stm_to_float(
            self._fsync_stm_read(self.FSYNC_STM_IN_FREQ_REG)
        )

    def fsync_controller_input_duty_cycle(self) -> float:
        return self._fsync_stm_to_float(
            self._fsync_stm_read(self.FSYNC_STM_IN_DUTY_REG)
        )


# ----------------------------------------------------------------
# FSYNC register map
# ----------------------------------------------------------------

ControllerBox.FSYNC_STM_FW_VERSION_REG = ControllerBox._fsync_stm_bin(0x00, 1)
ControllerBox.FSYNC_STM_UNLOCK_MAGIC = ControllerBox._fsync_stm_bin(42, 4)

ControllerBox.FSYNC_STM_CONFIG_REG = ControllerBox._fsync_stm_bin(0x01, 1)
ControllerBox.FSYNC_STM_CONFIG_REG_MASTER_INPUT = ControllerBox._fsync_stm_bin(0x00, 4)
ControllerBox.FSYNC_STM_CONFIG_REG_MASTER_OUTPUT = ControllerBox._fsync_stm_bin(0x01, 4)
ControllerBox.FSYNC_STM_CONFIG_REG_SLAVE_INPUT = ControllerBox._fsync_stm_bin(0x02, 4)
ControllerBox.FSYNC_STM_INTERNAL_FREQUENCY_REG = ControllerBox._fsync_stm_bin(0x02, 1)
ControllerBox.FSYNC_STM_ACTUAL_FREQUENCY_REG = ControllerBox._fsync_stm_bin(0x03, 1)
ControllerBox.FSYNC_STM_IN_PRESENT_REG = ControllerBox._fsync_stm_bin(0x04, 1)
ControllerBox.FSYNC_STM_IN_FREQ_REG = ControllerBox._fsync_stm_bin(0x05, 1)
ControllerBox.FSYNC_STM_IN_DUTY_REG = ControllerBox._fsync_stm_bin(0x06, 1)
ControllerBox.FSYNC_STM_OUTPUT_3_DUTY_CYCLE = ControllerBox._fsync_stm_bin(0x0E, 1)
ControllerBox.FSYNC_STM_OUTPUT_3_ACTIVE_LVL = ControllerBox._fsync_stm_bin(0x0F, 1)
ControllerBox.FSYNC_STM_OUTPUT_11_DUTY_CYCLE = ControllerBox._fsync_stm_bin(0x1E, 1)
ControllerBox.FSYNC_STM_OUTPUT_11_ACTIVE_LVL = ControllerBox._fsync_stm_bin(0x1F, 1)
ControllerBox.FSYNC_STM_OUTPUT_ACTIVE_LVL_LOW = ControllerBox._fsync_stm_bin(0x00, 4)
ControllerBox.FSYNC_STM_OUTPUT_ACTIVE_LVL_HIGH = ControllerBox._fsync_stm_bin(0x01, 4)
