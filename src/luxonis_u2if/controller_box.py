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
    # I2C
    # ----------------------------------------------------------------

    VALID_SDA_GPIO = (1, 5, 9, 13)
    VALID_SCL_GPIO = (2, 6, 10, 14)

    # ----------------------------------------------------------------
    # FSYNC CONTROLLER (legacy)
    # ----------------------------------------------------------------
    FSYNC_SDA = 28
    FSYNC_SCL = 29

    FSYNC_I2C_BUS = 0
    FSYNC_I2C_CLK_SPEED = 100000
    FSYNC_CONTROLLER_ADDR = 0x12
    FSYNC_CONTROLLER_DATA_ENDIAN = "<"

    # ----------------------------------------------------------------
    # FSYNC CONTROLLER
    # ----------------------------------------------------------------
  
    PIN_CONFIG_TYPE_HIGH_Z = 1
    PIN_CONFIG_TYPE_PWM = 2
    PIN_CONFIG_TYPE_ADC = 4
    PIN_CONFIG_TYPE_PWM_KEEPAWAKE = 8
    PIN_CONFIG_TYPE_PWM_HFSTROBE = 16

    fsync_bus = 0
    fsync_address = FSYNC_CONTROLLER_ADDR
    fsync_version = 14

    fsync_initialised = False

    fw_ver = 0

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

        reply = self.rp2040._hid_xfer(
            bytes([self.rp2040.FSYNC_PROBE]),
            True,
        )[1]

        if reply == self.rp2040.RESP_NOT_CONCERNED:
            self.fw_ver = 0
        else:
            self.fw_ver = 1
        
        if self.fw_ver == 1:
            fsync_probe_result = self.rp2040.fsync_probe()
            self.fsync_bus = fsync_probe_result[0]
            self.fsync_address = fsync_probe_result[1]
            self.fsync_version = fsync_probe_result[2]
            
    def close(self):
        self._running = False
        if self._btn_thread:
            self._btn_thread.join(timeout=0.1)
        self.rp2040.close()

    # ----------------------------------------------------------------
    # FSYNC helpers (legacy)
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
    # I2C
    # ----------------------------------------------------------------

    def i2c_init(self, baudrate: int, sda: int, scl: int, pullup: bool = False):
        if self.fsync_initialised and self.fsync_bus == 0:
            raise RuntimeError(
                "Cannot initialize I2C bus 0: FSYNC Controller is already initialized on bus 0."
            )

        if sda not in self.VALID_SDA_GPIO:
            raise ValueError(f"Invalid I2C SDA pin: {sda}")

        if scl not in self.VALID_SCL_GPIO:
            raise ValueError(f"Invalid I2C SCL pin: {scl}")

        sda_gpio = self.map_gpio(sda)
        scl_gpio = self.map_gpio(scl)
    
        self.rp2040.i2c_set_port(0)
        self.rp2040.i2c_configure(baudrate, sda_gpio, scl_gpio, pullup)

    def i2c_write(self, address: int, data, *, start: int = 0, end=None):
        """Write data to an I2C device on bus 0."""
        if self.rp2040._i2c_index != 0:
            raise RuntimeError("I2C bus 0 is not initialized.")
    
        if isinstance(data, list):
            data = bytes(data)
    
        self.rp2040.i2c_writeto(
            address,
            data,
            start=start,
            end=end,
        )
    
    def i2c_read(self, address: int, length: int) -> bytes:
        """Read a number of bytes from an I2C device on bus 0."""
        if self.rp2040._i2c_index != 0:
            raise RuntimeError("I2C bus 0 is not initialized.")
    
        buffer = bytearray(length)
    
        self.rp2040.i2c_readfrom_into(
            address,
            buffer,
        )
    
        return bytes(buffer)
    
    def i2c_write_read(
        self,
        address: int,
        write_data,
        read_length: int,
    ) -> bytes:
        """Write to an I2C device and perform a repeated-start read."""
        if self.rp2040._i2c_index != 0:
            raise RuntimeError("I2C bus 0 is not initialized.")
    
        if isinstance(write_data, list):
            write_data = bytes(write_data)
    
        read_buffer = bytearray(read_length)
    
        self.rp2040.i2c_writeto_then_readfrom(
            address,
            write_data,
            read_buffer,
        )
    
        return bytes(read_buffer)
    
    def i2c_scan(self, start: int = 0x08, end: int = 0x77):
        """Scan for I2C devices on bus 0."""
        if self.rp2040._i2c_index != 0:
            raise RuntimeError("I2C bus 0 is not initialized.")
    
        if not 0 <= start <= 0x7F:
            raise ValueError("Invalid I2C start address.")
    
        if not 0 <= end <= 0x7F:
            raise ValueError("Invalid I2C end address.")
    
        if start > end:
            raise ValueError("I2C start address must not be greater than end address.")
    
        return self.rp2040.i2c_scan(
            start=start,
            end=end,
        )
    
    # ----------------------------------------------------------------
    # FSYNC
    # ----------------------------------------------------------------
    def fsync_controller_get_pin_configuration(self, output: FsyncOutput) -> int:
        if self.fsync_address == self.rp2040.FSYNC_BOOT_ADDRESS:
            raise RuntimeError("FSYNC controller is in bootloader mode. Did you flash the FSYNC controller?")

        if output == self.FsyncOutput.ISOLATED_STROBE:
            fw_pin = self.rp2040.FSYNC_PIN_PB0_ID
        elif output == self.FsyncOutput.M8_FSYNC:
            fw_pin = self.rp2040.FSYNC_PIN_PA11_ID
        else:
            raise ValueError("Invalid FsyncOutput")
    
        if self.fw_ver == 1:
            return self.rp2040.fsync_get_pin_capabilities(fw_pin)
    
        raise NotImplementedError(
            "FSYNC pin configuration is not supported by the legacy interface."
        )
    
    def fsync_controller_set_pin_configuration(
        self, cfg: int, output: FsyncOutput
    ) -> int:
        if self.fsync_address == self.rp2040.FSYNC_BOOT_ADDRESS:
            raise RuntimeError("FSYNC controller is in bootloader mode. Did you flash the FSYNC controller?")

        if self.fsync_initialised:
            raise RuntimeError("FSYNC Controller already initialised, the configuration must be set before the fsync initialisation.")
    
        if output == self.FsyncOutput.ISOLATED_STROBE:
            fw_pin = self.rp2040.FSYNC_PIN_PB0_ID
        elif output == self.FsyncOutput.M8_FSYNC:
            fw_pin = self.rp2040.FSYNC_PIN_PA11_ID
        else:
            raise ValueError("Invalid FsyncOutput")
  
        mask = (self.PIN_CONFIG_TYPE_HIGH_Z 
        | self.PIN_CONFIG_TYPE_PWM 
        | self.PIN_CONFIG_TYPE_ADC 
        | self.PIN_CONFIG_TYPE_PWM_KEEPAWAKE
        | self.PIN_CONFIG_TYPE_PWM_HFSTROBE)

        if (cfg & (cfg - 1)) != 0 or (cfg & mask) == 0:
            raise ValueError("Invalid pin configuration")

        if self.fw_ver == 1:
            self.rp2040.fsync_set_pin_capabilities(fw_pin, cfg)
    
            actual = self.rp2040.fsync_get_pin_capabilities(fw_pin)
            if actual != cfg:
                raise RuntimeError("Failed to set FSYNC pin configuration")
    
            return actual
    
        raise NotImplementedError(
            "FSYNC pin configuration is not supported by the legacy interface."
        )

    def fsync_controller_init(self):
        if self.fsync_address == self.rp2040.FSYNC_BOOT_ADDRESS:
            raise RuntimeError("FSYNC controller is in bootloader mode. Did you flash the FSYNC controller?")

        use_fw_api = (
            self.fw_ver == 1
        )
        
        if self.rp2040._i2c_index == self.fsync_bus: 
            raise RuntimeError("I2C bus already reconfigured. But the FSYNC Controller uses this bus on this revision.")

        if use_fw_api:
            self.rp2040.fsync_init()
            self.rp2040.fsync_set_mode(self.rp2040.FSYNC_MODE_INPUT)

            if self.rp2040.fsync_get_mode() != self.rp2040.FSYNC_MODE_INPUT:
                raise RuntimeError("Failed to initialize FSYNC Controller")

            self.fsync_initialised = True
            return

        self.rp2040.i2c_set_port(self.FSYNC_I2C_BUS)
        self.rp2040.i2c_configure(
            self.FSYNC_I2C_CLK_SPEED, self.FSYNC_SDA, self.FSYNC_SCL
        )

        slaves = self.rp2040.i2c_scan(
            start=self.FSYNC_CONTROLLER_ADDR,
            end=self.FSYNC_CONTROLLER_ADDR + 1,
        )

        if self.FSYNC_CONTROLLER_ADDR not in slaves:
            raise RuntimeError("FSYNC Controller not found")

        self._fsync_stm_write(
            self.FSYNC_STM_CONFIG_REG
            + self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT
        )

        mode = self._fsync_stm_read(self.FSYNC_STM_CONFIG_REG)

        if mode != self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT:
            self._fsync_stm_write(
                self.FSYNC_STM_FW_VERSION_REG
                + self.FSYNC_STM_UNLOCK_MAGIC
            )

            self._fsync_stm_write(
                self.FSYNC_STM_CONFIG_REG
                + self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT
            )

            mode = self._fsync_stm_read(self.FSYNC_STM_CONFIG_REG)

        if mode != self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT:
            raise RuntimeError("Unable to unlock FSYNC Controller")

        self._fsync_stm_write(
            self.FSYNC_STM_CONFIG_REG
            + self.FSYNC_STM_CONFIG_REG_MASTER_INPUT
        )

        self.fsync_initialised = True

    def fsync_controller_set_mode(self, mode: FsyncMode):
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        if mode == self.FsyncMode.MASTER_INPUT:
            fw_mode = self.rp2040.FSYNC_MODE_INPUT
            legacy_mode = self.FSYNC_STM_CONFIG_REG_MASTER_INPUT
        elif mode == self.FsyncMode.MASTER_OUTPUT:
            fw_mode = self.rp2040.FSYNC_MODE_MASTER
            legacy_mode = self.FSYNC_STM_CONFIG_REG_MASTER_OUTPUT
        elif mode == self.FsyncMode.SLAVE:
            fw_mode = self.rp2040.FSYNC_MODE_SLAVE
            legacy_mode = self.FSYNC_STM_CONFIG_REG_SLAVE_INPUT
        else:
            raise ValueError("Invalid FsyncMode")

        use_fw_api = (
            self.fw_ver == 1
        )

        if use_fw_api:
            self.rp2040.fsync_set_mode(fw_mode)

            if self.rp2040.fsync_get_mode() != fw_mode:
                raise RuntimeError("Failed to set FsyncMode")
            return

        self._fsync_stm_write(
            self.FSYNC_STM_CONFIG_REG + legacy_mode
        )

        read_mode = self._fsync_stm_read(self.FSYNC_STM_CONFIG_REG)

        if read_mode != legacy_mode:
            raise RuntimeError("Failed to set FsyncMode")


    def fsync_controller_set_frequency(self, freq: float) -> float:
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        # Preserve the legacy public API validation (0..600 Hz).
        freq_to_set = self._fsync_stm_internal_frequency(freq)

        use_fw_api = (
            self.fw_ver == 1
        )

        if self.fw_ver == 1:
            self.rp2040.fsync_set_fps(freq)
            _, actual_freq = self.rp2040.fsync_get_fps()
            return actual_freq

        self._fsync_stm_write(
            self.FSYNC_STM_INTERNAL_FREQUENCY_REG
            + freq_to_set
        )

        actual_frq = self._fsync_stm_read(
            self.FSYNC_STM_ACTUAL_FREQUENCY_REG
        )

        return self._fsync_stm_to_float(actual_frq)


    def fsync_controller_set_duty_cycle(
        self, duty_cycle: float, output: FsyncOutput
    ) -> float:
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        if output == self.FsyncOutput.ISOLATED_STROBE:
            fw_pin = self.rp2040.FSYNC_PIN_PB0_ID
            fw_channel = self.rp2040.FSYNC_CHANNEL_PB0_ID
            legacy_output = self.FSYNC_STM_OUTPUT_3_DUTY_CYCLE
        elif output == self.FsyncOutput.M8_FSYNC:
            fw_pin = self.rp2040.FSYNC_PIN_PA11_ID
            fw_channel = self.rp2040.FSYNC_CHANNEL_PA11_ID
            legacy_output = self.FSYNC_STM_OUTPUT_11_DUTY_CYCLE
        else:
            raise ValueError("Invalid FsyncOutput")

        duty_cycle_to_set = self._fsync_stm_output_duty_cycle(
            duty_cycle
        )

        use_fw_api = (
            self.fw_ver == 1
        )

        if use_fw_api:
            duty_to_set = self._fsync_stm_to_int(
                duty_cycle_to_set
            )

            self.rp2040.fsync_set_duty(
                fw_channel, duty_to_set
            )

            cap = self.rp2040.fsync_get_pin_capabilities(fw_pin)

            if cap & self.PIN_CONFIG_TYPE_PWM_HFSTROBE:
                _, fps = self.rp2040.fsync_get_fps()
                polarity = self.rp2040.fsync_get_polarity(fw_channel)

                act_duty = duty_cycle / 100.0

                if polarity == 1:
                    act_duty = 1 - duty_cycle

                if act_duty + act_duty / fps * (1300 - fps) > 1:
                    max_duty = (1 / (1 + 1 / fps * (1300 - fps))) * 100
                    if polarity == 0:
                        raise ValueError(f"Input duty too high for high fps strobe for this frequency and negative polarity. Max is {max_duty} %")
                    else:
                        max_duty = 100 - max_duty
                        raise ValueError(f"Input duty too high for high fps strobe for this frequency and positive polarity. Min is {max_duty} %")

            actual = self.rp2040.fsync_get_duty(fw_channel)

            return 100.0 * actual / 2048.0

        self._fsync_stm_write(
            legacy_output + duty_cycle_to_set
        )

        actual = self._fsync_stm_to_int(
            self._fsync_stm_read(legacy_output)
        )

        return 100.0 * actual / 2048.0


    def fsync_controller_set_polarity(
        self, polarity: bool, output: FsyncOutput
    ):
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        if output == self.FsyncOutput.ISOLATED_STROBE:
            fw_channel = self.rp2040.FSYNC_CHANNEL_PB0_ID
            legacy_output = self.FSYNC_STM_OUTPUT_3_ACTIVE_LVL
        elif output == self.FsyncOutput.M8_FSYNC:
            fw_channel = self.rp2040.FSYNC_CHANNEL_PA11_ID
            legacy_output = self.FSYNC_STM_OUTPUT_11_ACTIVE_LVL
        else:
            raise ValueError("Invalid FsyncOutput")

        use_fw_api = (
            self.fw_ver == 1
        )

        if use_fw_api:
            self.rp2040.fsync_set_polarity(
                fw_channel, int(polarity)
            )
            return

        # Generate both values here because the current file only defines
        # FSYNC_STM_OUTPUT_ACTIVE_LVL_HIGH.
        polarity_to_set = self._fsync_stm_bin(
            1 if polarity else 0, 4
        )

        self._fsync_stm_write(
            legacy_output + polarity_to_set
        )


    def fsync_controller_input_detected(self) -> bool:
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        use_fw_api = (
            self.fw_ver == 1
        )

        if use_fw_api:
            present, _, _ = self.rp2040.fsync_get_input_info()
            return present

        present = self._fsync_stm_to_int(
            self._fsync_stm_read(
                self.FSYNC_STM_IN_PRESENT_REG
            )
        )

        if present == 0:
            return False
        elif present == 1:
            return True
        else:
            raise RuntimeError(
                f"Unexpected input present value: {present}"
            )


    def fsync_controller_input_frequency(self) -> float:
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        use_fw_api = (
            self.fw_ver == 1
        )

        if use_fw_api:
            _, freq, _ = self.rp2040.fsync_get_input_info()
            return freq

        return self._fsync_stm_to_float(
            self._fsync_stm_read(
                self.FSYNC_STM_IN_FREQ_REG
            )
        )


    def fsync_controller_input_duty_cycle(self) -> float:
        if not self.fsync_initialised:
            raise RuntimeError("FSYNC Controller not initialised.")

        use_fw_api = (
            self.fw_ver == 1
        )

        if use_fw_api:
            _, _, duty = self.rp2040.fsync_get_input_info()
            return 100.0 * duty / 2048.0

        return self._fsync_stm_to_float(
            self._fsync_stm_read(
                self.FSYNC_STM_IN_DUTY_REG
            )
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
ControllerBox.FSYNC_STM_OUTPUT_ACTIVE_LVL_HIGH = ControllerBox._fsync_stm_bin(0x01, 4)
