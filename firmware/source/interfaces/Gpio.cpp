#include "Gpio.h"

#include <string.h>
#include <algorithm>
#include "hardware/gpio.h"
#include "pca9555.h"

// à mettre en variables memebres ?
static const uint8_t MAX_BUFFERED_EVENT = 60;
static uint8_t irqEventBuffer[MAX_BUFFERED_EVENT];
static volatile uint8_t irqEventBufferCount = 0;
static critical_section_t critSec;

// Expander variables
static const uint8_t EXP0_BANK_OFFSET = 32;
static const uint8_t EXP1_BANK_OFFSET = 64;

// Debouncer variables
const uint8_t MAX_PINS = 30;
const uint8_t DEBOUNCE_PERIODS_MS = 1;
const uint8_t PRESS_PERIODS_MS = 3;
const uint8_t RELEASE_PERIODS_MS = 20;
static uint32_t debouncedEvtRisingList = 0x00;
static uint32_t debouncedEvtFallingList = 0x00;
static uint32_t debouncedStateList = 0x00;
static uint8_t debouncerCounterList[MAX_PINS];


void gpioCallback(uint gpio, uint32_t events) {
    uint8_t interfaceEvent = gpio & 0b00111111;
    if(events & GPIO_IRQ_EDGE_RISE)
        interfaceEvent |= IRQ_EVENT::EVENT_RISING << 6;
    if(events & GPIO_IRQ_EDGE_FALL)
        interfaceEvent |= IRQ_EVENT::EVENT_FALLING << 6;

    critical_section_enter_blocking(&critSec);
    if(irqEventBufferCount < MAX_BUFFERED_EVENT) {
        irqEventBuffer[irqEventBufferCount++] = interfaceEvent;
    }
    critical_section_exit(&critSec);
}

// debouncing : http://stackoverflow.com/questions/155071/simple-debounce-routine
bool debounceInput(repeating_timer_t *rt) {
    (void)rt;

    uint32_t rawStatePins = gpio_get_all();
    for(uint8_t gpio=0; gpio < MAX_PINS; gpio++){
        bool risingEv = !!(debouncedEvtRisingList & (1ul << gpio));
        bool fallingEv = !!(debouncedEvtFallingList & (1ul << gpio));
        if( !fallingEv && !risingEv)
            continue;

        bool rawState = !!((1ul << gpio) & rawStatePins);
        bool debouncedState = debouncedStateList & (0x01 << gpio);
        if(rawState == debouncedState){
            if(debouncedState)
                debouncerCounterList[gpio] = RELEASE_PERIODS_MS / DEBOUNCE_PERIODS_MS;
            else
                debouncerCounterList[gpio] = PRESS_PERIODS_MS / DEBOUNCE_PERIODS_MS;
        } else {
            // Key has changed - wait for new state to become stable.
            if (--(debouncerCounterList[gpio]) == 0) {
                // Timer expired - accept the change.
                uint8_t interfaceEvent = 0x00;
                if(rawState) {
                    debouncedStateList |= (1ul << gpio);
                    debouncerCounterList[gpio] = RELEASE_PERIODS_MS / DEBOUNCE_PERIODS_MS;
                    if(risingEv)
                        interfaceEvent |= IRQ_EVENT::EVENT_RISING << 6;
                } else {
                    debouncedStateList &= ~(1ul << gpio);
                    debouncerCounterList[gpio] = PRESS_PERIODS_MS / DEBOUNCE_PERIODS_MS;
                    if(fallingEv)
                        interfaceEvent |= IRQ_EVENT::EVENT_FALLING << 6;
                }

                if(interfaceEvent != 0x00) {
                    interfaceEvent |= (gpio & 0b00111111);
                    critical_section_enter_blocking(&critSec);
                    if(irqEventBufferCount < MAX_BUFFERED_EVENT) {
                        irqEventBuffer[irqEventBufferCount++] = interfaceEvent;
                    }
                    critical_section_exit(&critSec);
                }
            }
        }
    }

    return true;
}

Gpio::Gpio() {
    setInterfaceState(InterfaceState::INTIALIZED);
    critical_section_init(&critSec);

#if I2C1_ENABLED && (defined(PCA9555_0_ENABLED) || defined(PCA9555_1_ENABLED))
    // the pca expanders live on i2c bus 1
    i2c_init(i2c1, 100 * 1000);
    gpio_set_function(U2IF_I2C1_SDA, GPIO_FUNC_I2C);
    gpio_set_function(U2IF_I2C1_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(U2IF_I2C1_SDA);
    gpio_pull_up(U2IF_I2C1_SCL);
#endif

#if I2C0_ENABLED
    i2c_init(i2c0, 100 * 1000);
    gpio_set_function(U2IF_I2C0_SDA, GPIO_FUNC_I2C);
    gpio_set_function(U2IF_I2C0_SCL, GPIO_FUNC_I2C);
    gpio_pull_up(U2IF_I2C0_SDA);
    gpio_pull_up(U2IF_I2C0_SCL);
#endif

#if defined(PCA9555_0_ENABLED) || defined(PCA9555_1_ENABLED)
    // the hardware team made an oopsie woopsie, it lives on one of the two addresses
    uint8_t pca9555_1_addr = PCA9555_1_I2C_ADDRESS;
   
    if (!pca9555Exists(i2c1, PCA9555_1_I2C_ADDRESS))
        pca9555_1_addr = PCA9555_1_I2C_ADDRESS_ALTERNATE;

    exp0.init(i2c1, PCA9555_0_I2C_ADDRESS, PCA9555_0_INT_GPIO);
    exp1.init(i2c1, pca9555_1_addr, PCA9555_1_INT_GPIO);
#endif

    add_repeating_timer_us(-DEBOUNCE_PERIODS_MS * 1000, debounceInput, NULL, &_debounceTimer);
}

Gpio::~Gpio() {
}

#if defined(PCA9555_0_ENABLED) || defined(PCA9555_1_ENABLED)
bool Gpio::pca9555Exists(i2c_inst_t *i2c, uint8_t address) {
    constexpr uint8_t inputPort0Register = 0x00;
    uint8_t value = 0;

    // Set the PCA9555 register pointer.
    const int writeResult = i2c_write_timeout_us(
        i2c,
        address,
        &inputPort0Register,
        1,
        true,       // Keep control of the bus for the following read.
        1000
    );

    if(writeResult != 1) {
        return false;
    }

    // Verify that the device responds with readable register data.
    const int readResult = i2c_read_timeout_us(
        i2c,
        address,
        &value,
        1,
        false,
        1000
    );

    return readResult == 1;
}
#endif

CmdStatus Gpio::process(uint8_t const *cmd, uint8_t response[64]) {
    CmdStatus status = CmdStatus::NOT_CONCERNED;

    if(cmd[0] == Report::ID::GPIO_INIT_PIN) {
        status = initPin(cmd);
    } else if(cmd[0] == Report::ID::GPIO_SET_VALUE) {
        status = setPin(cmd);
    } else if(cmd[0] == Report::ID::GPIO_GET_VALUE) {
        status = getPin(cmd, response);
    } else if(cmd[0] == Report::ID::GPIO_SET_IRQ) {
        status = setIrq(cmd);
    } else if(cmd[0] == Report::ID::GPIO_GET_IRQ) {
        status = getIrq(cmd, response);
    }

    return status;
}

CmdStatus Gpio::task(uint8_t response[64]) {
    (void)response;

    CmdStatus status = CmdStatus::NOT_CONCERNED;
    return status;
}

CmdStatus Gpio::initPinGpio(uint8_t const *cmd) {
    const uint gp = cmd[1];
    const uint dir = cmd[2] == 0 ? GPIO_IN : GPIO_OUT;
    gpio_init(gp);
    gpio_set_dir(gp, dir);

    if(dir == GPIO_IN && cmd[3] == 1) {
        gpio_pull_up(gp);
    } else if(dir == GPIO_IN && cmd[3] == 2) {
        gpio_pull_down(gp);
    } else if (dir == GPIO_IN) {
        gpio_disable_pulls(gp);
    }
    //a voir gpio_set_outover(gpio, GPIO_OVERRIDE_INVERT);
    return CmdStatus::OK;
}


CmdStatus Gpio::initPinExp(uint8_t const *cmd) {
    const uint gp = cmd[1];

    if(gp < EXP1_BANK_OFFSET) {
    #ifdef PCA9555_0_ENABLED
        const uint exp0_pin = gp - EXP0_BANK_OFFSET;
        const uint dir = cmd[2] == 0 ? GPIO_IN : GPIO_OUT;

        // Only direction is supported, PU/PD is not
        if(dir == GPIO_IN) {
            exp0.set_pin_mode(exp0_pin, 1);
        } else {
            exp0.set_pin_mode(exp0_pin, 0);
        }
    #endif
    } else {
    #ifdef PCA9555_1_ENABLED
        const uint exp1_pin = gp - EXP1_BANK_OFFSET;
        const uint dir = cmd[2] == 0 ? GPIO_IN : GPIO_OUT;

        // Only direction is supported, PU/PD is not
        if(dir == GPIO_IN) {
            exp1.set_pin_mode(exp1_pin, 1);
        } else {
            exp1.set_pin_mode(exp1_pin, 0);
        }
    #endif
    }

    return CmdStatus::OK;
}


CmdStatus Gpio::initPin(uint8_t const *cmd) {
    const uint gp = cmd[1];

    // Which GPIO block
    if(gp < EXP0_BANK_OFFSET) {
        return initPinGpio(cmd);
    } else {
        return initPinExp(cmd);
    }

    return CmdStatus::OK;
}

CmdStatus Gpio::setPinGpio(uint8_t const *cmd) {
    const uint gp = cmd[1];
    bool value = cmd[2] == 0 ? false : true;
    gpio_put(gp, value);
    return CmdStatus::OK;
}

CmdStatus Gpio::setPinExp(uint8_t const *cmd) {
    const uint gp = cmd[1];

    if(gp < EXP1_BANK_OFFSET) {
    #ifdef PCA9555_0_ENABLED
        const int exp0_pin = gp - EXP0_BANK_OFFSET;
        exp0.set_pin_value(exp0_pin, cmd[2]);
    #endif
    } else {
    #ifdef PCA9555_1_ENABLED
        const int exp1_pin = gp - EXP1_BANK_OFFSET;
        exp1.set_pin_value(exp1_pin, cmd[2]);
    #endif
    }

    return CmdStatus::OK;
}

CmdStatus Gpio::setPin(uint8_t const *cmd) {
    const uint gp = cmd[1];
    if(gp < EXP0_BANK_OFFSET) {
        return setPinGpio(cmd);
    } else {
        return setPinExp(cmd);
    }

    return CmdStatus::OK;
}

CmdStatus Gpio::getPin(uint8_t const *cmd, uint8_t response[64]) {
    const uint8_t gp = cmd[1];
    response[2] = gp;
    response[3] = gpio_get(gp);
    return CmdStatus::OK;
}

CmdStatus Gpio::setIrq(uint8_t const *cmd) {
    const uint gpio = cmd[1];
    const uint8_t ev = cmd[2];
    bool debounced = cmd[3] == 0x01 ? true : false;
    uint8_t event_flags = 0;
    if(ev & IRQ_EVENT::EVENT_RISING)
        event_flags |= GPIO_IRQ_EDGE_RISE;
    if(ev & IRQ_EVENT::EVENT_FALLING)
        event_flags |= GPIO_IRQ_EDGE_FALL;

    critical_section_enter_blocking(&critSec);
    // Remove previous irq settings if exists
    gpio_set_irq_enabled(gpio, GPIO_IRQ_EDGE_RISE | GPIO_IRQ_EDGE_FALL, false);
    debouncedEvtFallingList &= ~(1ul << gpio);
    debouncedEvtRisingList &= ~(1ul << gpio);

    if(event_flags != 0 && !debounced) {
        gpio_set_irq_enabled_with_callback(gpio, event_flags, true, gpioCallback);
    } else if(event_flags != 0) {
        if(ev & IRQ_EVENT::EVENT_FALLING)
            debouncedEvtFallingList |= 1ul << gpio;
        if(ev & IRQ_EVENT::EVENT_RISING)
            debouncedEvtRisingList |= 1ul << gpio;

        if(gpio_get(gpio))
            debouncedStateList |= (0x01 << gpio);
        else
            debouncedStateList &= ~(1ul << gpio);
    }
    critical_section_exit(&critSec);
    return CmdStatus::OK;
}

// TODO: To rework, it is a simple version with buffer smaller than HID response.
// It is necessary to be able to have larger buffers. Currently they are the size of the HID response.
CmdStatus Gpio::getIrq(uint8_t const *cmd, uint8_t response[64]) {
    (void)cmd;
    static uint32_t eventBufferCopy[MAX_BUFFERED_EVENT];
    static uint8_t eventBufferCountCopy = 0;

    if(eventBufferCountCopy == 0) {
        critical_section_enter_blocking(&critSec);
        eventBufferCountCopy = irqEventBufferCount;
        memcpy(eventBufferCopy, irqEventBuffer, sizeof(uint32_t) * eventBufferCountCopy);
        irqEventBufferCount = 0;
        critical_section_exit(&critSec);
    }

    response[2] = eventBufferCountCopy;
    memcpy(&(response[3]), eventBufferCopy, sizeof(uint8_t) * eventBufferCountCopy);
    eventBufferCountCopy = 0;
    return CmdStatus::OK;
}


