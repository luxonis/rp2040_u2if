#!/bin/bash

openocd -c "source [find interface/stlink.cfg]; source [find target/stm32g0x.cfg]" -c "program fsync_stm_firmware_g0_15.elf verify reset exit"
