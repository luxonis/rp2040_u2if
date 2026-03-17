import time
import threading
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

    #LEDs and Buttons
    LED_PINS = [17, 16, 18]
    BUTTON_PINS = [19, 20, 21]


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

        return [
            (self.REV_GPIO_MAP.get(gpio, gpio), event)
            for gpio, event in events
        ]

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
                pinA,
                self.rp2040.GPIO_OUT,
                self.rp2040.GPIO_PULL_NONE
            )

            self.rp2040.gpio_init_pin(
                pinB,
                self.rp2040.GPIO_OUT,
                self.rp2040.GPIO_PULL_NONE
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
        self._btn_map = {
            pin: i + 1
            for i, pin in enumerate(self.BUTTON_PINS)
        }

        for pin in self.BUTTON_PINS:

            self.rp2040.gpio_init_pin(
                pin,
                self.rp2040.GPIO_IN,
                self.rp2040.GPIO_PULL_NONE
            )

            self.rp2040.gpio_set_irq(
                pin,
                self.rp2040.IRQ_EVENT_RISING |
                self.rp2040.IRQ_EVENT_FALLING,
                True
            )

        self._running = True

        self._btn_thread = threading.Thread(
            target=self._button_event_loop,
            daemon=True
        )

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
                pin,
                self.rp2040.GPIO_OUT,
                self.rp2040.GPIO_PULL_NONE
            )
            self.rp2040.gpio_set_pin(pin, 0)  # start OFF

    def led_on(self, index):
        """Turn LED on."""
        self.rp2040.gpio_set_pin(self.LED_PINS[index-1], 1)


    def led_off(self, index):
        """Turn LED off."""
        self.rp2040.gpio_set_pin(self.LED_PINS[index-1], 0)


    def led_set(self, index, state):
        """Set LED state."""
        self.rp2040.gpio_set_pin(self.LED_PINS[index-1], int(state))


    
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

