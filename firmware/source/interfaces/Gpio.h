#ifndef _INTERFACE_GPIO_H
#define _INTERFACE_GPIO_H

#include "PicoInterfacesBoard.h"
#include "BaseInterface.h"
#include "pico/sync.h"

#if defined(PCA9555_0_ENABLED) || defined(PCA9555_1_ENABLED)
#include "pca9555.h"
#endif

class Gpio : public BaseInterface {
public:
    Gpio();
    virtual ~Gpio();

    CmdStatus process(uint8_t const *cmd, uint8_t response[64]);
    CmdStatus task(uint8_t response[64]);

protected:
    CmdStatus initPin(uint8_t const *cmd);
    CmdStatus setPin(uint8_t const *cmd);
    CmdStatus getPin(uint8_t const *cmd, uint8_t response[64]);
    CmdStatus setIrq(uint8_t const *cmd);
    CmdStatus getIrq(uint8_t const *cmd, uint8_t response[64]);
private:
    repeating_timer_t _debounceTimer;

#if defined(PCA9555_0_ENABLED) || defined(PCA9555_1_ENABLED)
    bool pca9555Exists(i2c_inst_t *i2c, uint8_t address);
#endif
    CmdStatus initPinGpio(uint8_t const *cmd);
    CmdStatus initPinExp(uint8_t const *cmd);
    CmdStatus setPinGpio(uint8_t const *cmd);
    CmdStatus setPinExp(uint8_t const *cmd);
    CmdStatus getPinGpio(uint8_t const *cmd, uint8_t response[64]);
    CmdStatus getPinExp(uint8_t const *cmd, uint8_t response[64]);

#ifdef PCA9555_0_ENABLED
    pca9555 exp0;
#endif
#ifdef PCA9555_1_ENABLED
    pca9555 exp1;
#endif
};


#endif
