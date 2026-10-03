cmake_minimum_required(VERSION 3.12)

option(IS_1V8 "Are you compiling for a 1V8 board?" OFF)
option(ENABLE_STDIO_USB OFF)
option(ENABLE_STDIO_UART OFF)

set(BUILD_NAME "u2if")

# Following two lines needed to make W25Q128 1V8 flash working
# First we need to prescale SPI frequency by factor 4 to mitigate flash read errors
add_compile_definitions(PICO_FLASH_SPI_CLKDIV=4)

# Second stage bootloader needs to be changed because our flash is qualified as "generic" flash which uses 0x3h command to read data
set(PICO_DEFAULT_BOOT_STAGE2_FILE ${CMAKE_CURRENT_SOURCE_DIR}/../pico-sdk/src/rp2_common/boot_stage2/boot2_generic_03h.S)

if(IS_1V8)
        message(WARNING "IS_1V8=ON, Configuring for 1V8 board - Caution if your board is not 1V8, you may damage it!")
        add_compile_definitions(PICO_1V8=1)
        set(BUILD_NAME "u2if_${BOARD}")
else ()
        set(BUILD_NAME "u2if_${BOARD}")
        message(STATUS "Configuring for 3V3 board")
endif()



# If you want to flash directly to RAM
# NOTE: Didn't boot for me - didn't debug too much
# set(PICO_NO_FLASH 1)
# set(PICO_COPY_TO_RAM 0)

# Set PICO_SDK_PATH to parent directory
get_filename_component(PICO_SDK_PATH "${CMAKE_CURRENT_LIST_DIR}/../pico-sdk" ABSOLUTE)

# initialize the SDK based on PICO_SDK_PATH
# note: this must happen before project()
include(pico_sdk_import.cmake)

project(${BUILD_NAME} VERSION "0.6.0")

# initialize the Pico SDK
pico_sdk_init()

set(BOARD "CUSTOM" CACHE STRING "BaseName chosen by the user at CMake configure time")
set_property(CACHE BOARD PROPERTY STRINGS PICO FEATHER ITSYBITSY QTPY QT2040_TRINKEY SL6945_1V8 MD6976_R2 SL69008_1V8 SL6925_1V8 SL6925_3V3)
message(STATUS "Selected board:'${BOARD}'")

# might help for feather?
#add_compile_definitions(PICO_DEFAULT_BOOT_STAGE2_FILE=${CMAKE_CURRENT_SOURCE_DIR}/../pico-sdk/src/rp2_common/boot_stage2/boot2_generic_03h.S)

if (NOT DEFINED ADC_ENABLED)
        set(ADC_ENABLED 1)
endif()

if (NOT DEFINED PWM_ENABLED)
        set(PWM_ENABLED 1)
endif()

if (NOT DEFINED I2S_ALLOW)
        set(I2S_ALLOW 0)
endif()

if (NOT DEFINED HUB75_ALLOW)
        set(HUB75_ALLOW 0)
endif()

if (NOT DEFINED WS2812_SIZE)
        set(WS2812_SIZE 1000)
endif()

if (NOT DEFINED WS2812_ENABLED)
        set(WS2812_ENABLED 1)
endif()

if (NOT DEFINED HUB75_MAX_LEDS)
        set(HUB75_MAX_LEDS 128*64)
endif()


configure_file("${PROJECT_SOURCE_DIR}/board_config.h.in" "include/board_config.h")

FILE(GLOB InterfaceSources interfaces/*.cpp)

add_executable(${BUILD_NAME}
        main.cpp
        usb_descriptors.c
	ModeActivity.cpp
	${InterfaceSources}
        )

# If you want to flash directly to RAM
# NOTE: Didn't boot for me - didn't debug too much
# pico_set_binary_type(u2if no_flash)
# pico_set_linker_script(u2if /home/pi/pico/u2if/firmware/pico-sdk/src/rp2_common/pico_standard_link/memmap_no_flash.ld)

# generate the header file into the source tree as it is included in the RP2040 datasheet
pico_generate_pio_header(${BUILD_NAME} ${CMAKE_CURRENT_LIST_DIR}/interfaces/ws2812.pio OUTPUT_DIR ${CMAKE_CURRENT_LIST_DIR}/interfaces/)
pico_generate_pio_header(${BUILD_NAME} ${CMAKE_CURRENT_LIST_DIR}/interfaces/audio_i2s.pio OUTPUT_DIR ${CMAKE_CURRENT_LIST_DIR}/interfaces/)
pico_generate_pio_header(${BUILD_NAME} ${CMAKE_CURRENT_LIST_DIR}/interfaces/hub75.pio OUTPUT_DIR ${CMAKE_CURRENT_LIST_DIR}/interfaces/)

target_include_directories(${BUILD_NAME} PRIVATE "${CMAKE_CURRENT_BINARY_DIR}/include")
target_include_directories(${BUILD_NAME} PRIVATE ${CMAKE_CURRENT_LIST_DIR})

target_link_libraries(${BUILD_NAME} PRIVATE pico_stdlib pico_unique_id tinyusb_device tinyusb_board
hardware_i2c hardware_watchdog hardware_pwm hardware_adc hardware_spi
hardware_pio hardware_dma pico_sync pico_multicore)

pico_enable_stdio_usb(${BUILD_NAME} ${ENABLE_STDIO_USB})
pico_enable_stdio_uart(${BUILD_NAME} ${ENABLE_STDIO_UART}) # Set to 1, call stdio_init_all(); to make printf for debugging puroposes

pico_add_extra_outputs(${BUILD_NAME})

# add url via pico_set_program_url
#example_auto_set_url(${BUILD_NAME})

add_subdirectory(pca9555)

target_link_libraries(${BUILD_NAME} PRIVATE PCA9555)
