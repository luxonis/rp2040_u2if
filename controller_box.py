import time


class ControllerBox:
    """
    Hardware abstraction layer for the Controller Box.

    This class wraps the RP2040_u2if interface and provides a simple,
    board-oriented API for interacting with the Controller Box hardware.
    It handles logical GPIO remapping and exposes helper functions for
    controlling relays, panel LEDs, and reading panel buttons.
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

    # Relays
    RELAY_PINS = {
        1: (64, 65),
        2: (66, 67),
        3: (68, 69),
        4: (70, 71),
    }

    RELAY_PULSE = 0.02

    #LEDs and Buttons
    PANEL_LED_PINS = [17, 16, 18]
    PANEL_BUTTON_PINS = [19, 20, 21]


    def __init__(self, rp2040):
        """
        Parameters
        ----------
        rp2040 : RP2040_u2if
            Existing RP2040 interface object
        """
        self.rp2040 = rp2040

    # ----------------------------------------------------------------
    # GPIO REMAPPING
    # ----------------------------------------------------------------

    def map_gpio(self, pin):
        """
        Translate logical GPIO to RP2040 physical pin.
        """
        return self.GPIO_MAP.get(pin, pin)

    # ----------------------------------------------------------------
    # GPIO WRAPPERS
    # ----------------------------------------------------------------

    def gpio_init(self, pin, direction, pull):
        """
        Initialize GPIO using logical pin numbers.
        """
        pin = self.map_gpio(pin)
        self.rp2040.gpio_init_pin(pin, direction, pull)

    def gpio_set(self, pin, value):
        """
        Set GPIO value using logical pin numbers.
        """
        pin = self.map_gpio(pin)
        self.rp2040.gpio_set_pin(pin, value)

    def gpio_get(self, pin):
        """
        Read GPIO value using logical pin numbers.
        """
        pin = self.map_gpio(pin)
        return self.rp2040.gpio_get_pin(pin)

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
    # PANEL (LEDs + Buttons)
    # ----------------------------------------------------------------

    def panel_init(self):
        """Initialize LEDs and buttons."""

        if len(self.PANEL_LED_PINS) != len(self.PANEL_BUTTON_PINS):
            raise ValueError("LED and button arrays must be same length")

        # State tracking
        self._prev_states = [False] * len(self.PANEL_BUTTON_PINS)
        self._current_states = [False] * len(self.PANEL_BUTTON_PINS)

        # LEDs as outputs
        for pin in self.PANEL_LED_PINS:
            self.rp2040.gpio_init_pin(
                pin,
                self.rp2040.GPIO_OUT,
                self.rp2040.GPIO_PULL_NONE
            )
            self.rp2040.gpio_set_pin(pin, 0)

        # Buttons as inputs
        for pin in self.PANEL_BUTTON_PINS:
            self.rp2040.gpio_init_pin(
                pin,
                self.rp2040.GPIO_IN,
                self.rp2040.GPIO_PULL_NONE
            )

        # Initialize button state cache
        for i, pin in enumerate(self.PANEL_BUTTON_PINS):
            state = self.rp2040.gpio_get_pin(pin)
            self._prev_states[i] = state
            self._current_states[i] = state


    # ------------------------------------------------------------
    # BUTTON SCAN
    # ------------------------------------------------------------

    def panel_scan(self):
        """
        Update button states.
        Call once per loop before reading buttons.
        """
        for i, pin in enumerate(self.PANEL_BUTTON_PINS):
            self._prev_states[i] = self._current_states[i]
            self._current_states[i] = self.rp2040.gpio_get_pin(pin)


    # ------------------------------------------------------------
    # LED CONTROL
    # ------------------------------------------------------------

    def led_on(self, index):
        """Turn LED on."""
        self.rp2040.gpio_set_pin(self.PANEL_LED_PINS[index], 1)


    def led_off(self, index):
        """Turn LED off."""
        self.rp2040.gpio_set_pin(self.PANEL_LED_PINS[index], 0)


    def led_set(self, index, state):
        """Set LED state."""
        self.rp2040.gpio_set_pin(self.PANEL_LED_PINS[index], int(state))


    # ------------------------------------------------------------
    # BUTTON READING (CACHED)
    # ------------------------------------------------------------

    def button_pressed(self, index):
        """
        Return True if button is pressed.

        Uses cached state from panel_scan().
        """
        return self._current_states[index]


    def read_all_buttons(self):
        """Return list of all button states (cached)."""
        return list(self._current_states)


    # ------------------------------------------------------------
    # EVENT DETECTION
    # ------------------------------------------------------------

    def button_pressed_event(self, index):
        """
        True once when button transitions
        released -> pressed.
        """
        return (not self._prev_states[index]) and self._current_states[index]


    def button_released_event(self, index):
        """
        True once when button transitions
        pressed -> released.
        """
        return self._prev_states[index] and (not self._current_states[index])


    # ------------------------------------------------------------
    # MIRROR BUTTONS - CONVENIENCE
    # ------------------------------------------------------------

    def mirror_buttons_to_leds(self):
        """LED turns on when button is pressed."""
        for i in range(len(self.PANEL_BUTTON_PINS)):
            self.led_set(i, self._current_states[i])

    
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

