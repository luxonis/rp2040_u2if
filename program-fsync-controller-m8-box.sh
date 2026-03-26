#!/bin/bash

BOOTLOADER_I2C_ADDR=0x56

STM32FLASH="/usr/bin/stm32flash"
I2C_GET="/usr/sbin/i2cget"
I2C_DETECT="/usr/sbin/i2cdetect"
STM_UTIL="/usr/bin/stm-util"

CMD_GET_VERSION="0x00"

hex_to_dec() {
    local hex=$1
    hex=${hex#0x}
    echo $((16#$hex))
}

dec_to_hex() {
    local dec=$1
    printf "0x%02x" $dec
}

find_i2c_bus_addr_by_compatible() {
    I2C_BUS="0"
    I2C_ADDR="0x12"
    export I2C_DEV="/dev/i2c-$I2C_BUS"
    export I2C_BUS I2C_ADDR
    return 0
}

get_version() {
    local response=$($I2C_GET -y -f $I2C_BUS $I2C_ADDR $CMD_GET_VERSION)
    if [ $? -ne 0 ]; then
        echo "Error getting firmware version"
        return 1
    fi

    local version=$(echo $response | awk '{print $1}')

    if [[ "$version" == 0x* ]]; then
        local version_dec=$(hex_to_dec $version)
        echo "Firmware version: $version ($version_dec)"
        return 0
    else
        echo "Error: Invalid version value"
        return 1
    fi
}

reset_board() {
    python ./set_prog_state.py 0
    sleep 1
    python ./set_prog_state.py 1
}

enter_bootloader() {
    python ./set_prog_state.py 0
    if $I2C_DETECT -y -r $I2C_BUS $BOOTLOADER_I2C_ADDR $BOOTLOADER_I2C_ADDR \
       | grep -qE "(^|[[:space:]])("${BOOTLOADER_I2C_ADDR#0x}")([[:space:]]|$)"; then
        
        echo "Device in bootloader mode"
        return 0
    else
        echo  "Failed to detect device in bootloader mode!"
        return 1
    fi
    
}

exit_bootloader() {
    python ./set_prog_state.py 1
}

program_stm() {
    local program_max_retries=3

    local flashing_success=0
    local count=1
    while [ $count -le $program_max_retries ]; do
        # Disable flash write protection
        "${STM32FLASH}" -a "${BOOTLOADER_I2C_ADDR}" "${I2C_DEV}"

        if [ $? -eq 0 ]; then
            flashing_success=1
            break
        fi

        sleep 0.1
        ((count++))
    done

    if [ $flashing_success -eq 0 ]; then
        echo "Disabling flash write protection failed."
        return 1
    fi

    # Generate option bytes bin file
    # echo "aafeffee" | xxd -r -p - /tmp/stm_options.bin
    printf '%b' '\xaa\xfe\xff\xee' > /tmp/stm_options.bin

    flashing_success=0
    count=1
    while [ $count -le $program_max_retries ]; do
        # Read option device's option bytes
        "${STM32FLASH}" -a "${BOOTLOADER_I2C_ADDR}" -r /tmp/stm_options_device.bin -S 0x1FFF7800:4 "${I2C_DEV}"

        if [ $? -eq 0 ]; then
            flashing_success=1
            break
        fi

        sleep 0.1
        ((count++))
    done

    if [ $flashing_success -eq 0 ]; then
        echo "Reading device option bytes failed."
        return 1
    fi

    # Only program if they are different to avoid unnecessary writes to the STM32 device
    if ! cmp -s /tmp/stm_options.bin /tmp/stm_options_device.bin; then

        flashing_success=0
        count=1
        while [ $count -le $program_max_retries ]; do
            "${STM32FLASH}" -a "${BOOTLOADER_I2C_ADDR}" -w /tmp/stm_options.bin -S 0x1FFF7800:4 "${I2C_DEV}"

            if [ $? -eq 0 ]; then
                flashing_success=1
                break
            fi

            sleep 0.1
            ((count++))
        done

        if [ $flashing_success -eq 0 ]; then
            echo "Flashing device option bytes failed."
            return 1
        fi

        flashing_success=0
        count=1
        while [ $count -le $program_max_retries ]; do
            "${STM32FLASH}" -a "${BOOTLOADER_I2C_ADDR}" -r /tmp/stm_options_verify.bin -S 0x1FFF7800:4 "${I2C_DEV}"

            if [ $? -eq 0 ]; then
                flashing_success=1
                break
            fi

            sleep 0.1
            ((count++))
        done

        if [ $flashing_success -eq 0 ]; then
            echo "Reading device option bytes failed."
            return 1
        fi

        if ! cmp -s /tmp/stm_options.bin /tmp/stm_options_verify.bin; then
            echo "STM32 FSync controller Option bytes verification failed!"
            rm /tmp/stm_options.bin /tmp/stm_options_device.bin /tmp/stm_options_verify.bin
            exit 1
        else
            echo "STM32 FSync controller Option bytes successfully programmed and verified"
            rm /tmp/stm_options_verify.bin
        fi
    else
        echo "STM32 FSync controller Option bytes already match"
    fi

    # Clean up the generated file
    rm /tmp/stm_options.bin /tmp/stm_options_device.bin

    flashing_success=0
    count=1
    while [ $count -le $program_max_retries ]; do
        # Flash the main flash memory with FW
        "${STM32FLASH}" -a "${BOOTLOADER_I2C_ADDR}" -w "$1" -v -g 0 -R "${I2C_DEV}"

        if [ $? -eq 0 ]; then
            flashing_success=1
            break
        fi

        sleep 0.1
        ((count++))
    done

    if [ $flashing_success -eq 0 ]; then
        echo "Flashing device main flash memory failed."
        return 1
    fi

    echo "STM32 FSync controller successfully programmed."

    # Note: We don't call exit_bootloader here because the -R flag in stm32flash
    # already resets the device. We'll load the kernel module separately.
    return 0
}

latest_firmware() {
    # Check for device type first
    local device_type
    if ${STM_UTIL} read type &>/dev/null; then
        device_type=$(${STM_UTIL} read type)
        case "$device_type" in
            0)
                device_type="c0"
                ;;
            1)
                device_type="g0"
                ;;
            *)
                echo "Unknown device type: $device_type" >&2
                return 1
                ;;
        esac
    else
        # Default to g0 if stm-util is not available
        device_type="g0"
    fi

    echo $(find /lib/firmware/ -maxdepth 1 -type f -name "fsync_stm_firmware_${device_type}_*.bin" | awk -F'[_.]' '{ printf "0x%s %s\n", $(NF-1), $0 }' | sort -k1,1nr | head -n1 | cut -d' ' -f2-)
}

check_device_presence() {
    # First check if device is in fsync mode
    $I2C_GET -y -f $I2C_BUS $I2C_ADDR $CMD_GET_VERSION > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "Device found in fsync mode at address $I2C_ADDR"
        return 0
    fi

    # Then check if device is in bootloader mode
    i2c_devices=$($I2C_DETECT -y -r "${I2C_BUS}")
    echo "$i2c_devices" | grep -q " ${BOOTLOADER_I2C_ADDR#0x} "
    if [ $? -eq 0 ]; then
        echo "Device found in bootloader mode at address $BOOTLOADER_I2C_ADDR"
        return 1
    fi

    echo "Device not found on I2C bus"
    return 2
}

verify_firmware_version() {
    local expected_version=$1

    if ! [[ "$expected_version" =~ ^[0-9]+$ ]]; then
        echo "Error: Expected version must be a number, got: $expected_version"
        return 1
    fi

    local response=$($I2C_GET -y -f $I2C_BUS $I2C_ADDR $CMD_GET_VERSION)
    if [ $? -ne 0 ]; then
        echo "Error getting firmware version for verification"
        return 1
    fi

    local actual_version=$(echo $response | awk '{print $1}')
    local actual_version_dec=$(hex_to_dec $actual_version)

    echo "Verifying firmware version: Expected $expected_version, Actual $actual_version_dec"

    if [ "$actual_version_dec" -eq "$expected_version" ]; then
        echo "Firmware version verification successful"
        return 0
    else
        echo "Firmware version verification failed"
        return 1
    fi
}

update_stm32_firmware() {
    local recovery_max_retries=3
    local count=1
    local recovery_success=0
    
    while [ $count -le $recovery_max_retries ]; do
        enter_bootloader
        
        if [ $? -ne 0 ]; then
            echo "STM32 not in bootloader mode"

            sleep 0.1
            ((count++))
            continue
        fi

        program_stm $1

        if [ $? -ne 0 ]; then
            echo "STM32 flashing failed"

            sleep 0.1
            ((count++))
            continue
        fi

        verify_firmware_version $2
        if [ $? -ne 0 ]; then
            echo "STM32 was programmed with incorrect firmware version."
        fi

        # Let the kenel module know that the STM32 is programmed
        python ./set_prog_state.py 1
        recovery_success=1
        break
    done

    if [ $recovery_success -eq 0 ]; then
        echo "STM32 recovery failed"

        return 1
    fi

    return 0
}

update_firmware() {
    local firmware_path=$1
    local file_version=$2
    local force_update=$3

    echo "Using firmware file: $firmware_path"
    if [ "$file_version" != "0" ]; then
        echo "Firmware version: $file_version"
    fi

    check_device_presence
    local device_status=$?

    if [ $device_status -eq 0 ]; then
        # Device is in normal mode, check firmware version
        local response=$($I2C_GET -y -f $I2C_BUS $I2C_ADDR $CMD_GET_VERSION)
        local version=$(echo $response | awk '{print $1}')
        local stm_version=$(hex_to_dec ${version#0x})
        echo "STM32 Fsync controller detected with firmware version $stm_version..."

        if [ "$force_update" = "true" ]; then
            echo "Forcing update with specified firmware file [$file_version]."
            update_stm32_firmware $firmware_path $file_version
        elif [ $stm_version -eq $file_version ]; then
            echo "STM32 FSync controller firmware version match. No update required."
        elif [ $stm_version -lt $file_version ]; then
            echo "STM32 FSync controller firmware version is older than latest available [$file_version]."
            update_stm32_firmware $firmware_path $file_version
        elif [ $stm_version -gt $file_version ]; then
            echo "STM32 FSync controller firmware version is newer than latest available [$file_version]."
            update_stm32_firmware $firmware_path $file_version
        fi
    else
        echo "STM32 FSync controller is not detected. Enter recovery..."
        update_stm32_firmware $firmware_path $file_version
    fi

    return $?
}

flash_device() {
    local custom_file=$1
    echo "Starting STM32 Fsync controller programming script..."
    sleep 1

    local firmware_path
    local file_version
    local force_update="false"

    if [ -n "$custom_file" ]; then
        if [ ! -f "$custom_file" ]; then
            echo "Error: Specified firmware file not found: $custom_file"
            exit 1
        fi
        firmware_path=$custom_file
        file_version=$(echo "$firmware_path" | sed -E 's/.*_([0-9a-f]+)\.bin$/\1/')
        if [[ "$file_version" =~ ^[0-9a-f]+$ ]] && ! [[ "$file_version" =~ ^[0-9]+$ ]]; then
            file_version=$((16#$file_version))
        fi
        force_update="true"  # Force update when a custom file is specified
    else
        latest_file=$(latest_firmware)

        if [ -z "$latest_file" ]; then
            echo "No fsync_stm_firmware file found. Exiting..."
            exit 1
        fi

        firmware_path=$latest_file
        file_version=$(echo "$firmware_path" | sed -E 's/.*_([0-9a-f]+)\.bin$/\1/')
        if [[ "$file_version" =~ ^[0-9a-f]+$ ]] && ! [[ "$file_version" =~ ^[0-9]+$ ]]; then
            file_version=$((16#$file_version))
        fi
    fi

    update_firmware "$firmware_path" "$file_version" "$force_update"
    if [ $? -ne 0 ]; then
        exit 1
    fi
}

startup() {
    echo "Performing startup check of STM32 FSync controller..."

    local latest_file=$(latest_firmware)
    if [ -z "$latest_file" ]; then
        echo "No fsync_stm_firmware file found. Exiting..."
        exit 1
    fi

    local firmware_path=$latest_file
    local file_version=$(echo "$firmware_path" | sed -E 's/.*_([0-9]+)\.bin$/\1/')
    echo "Latest firmware file: $firmware_path (version $file_version)"

    update_firmware "$firmware_path" "$file_version" "false"
    if [ $? -ne 0 ]; then
        rmmod fsync-stm
        exit 1
    fi

    echo "STM32 FSync controller startup check completed successfully."
}

usage() {
    echo "Usage: $0 <command> [args]"
    echo
    echo "System Commands:"
    echo "  startup                     Perform check of the firmware and update if needed"
    echo "  version                     Get firmware version"
    echo "  reset                       Reset the board"
    echo "  bootloader                  Enter bootloader mode"
    echo "  bootloader-exit             Exit bootloader mode"
    echo "  flash [file]                Flash firmware to the board (optional file path)"
    echo "  find                        Find the fsync-stm device"
}

find_i2c_bus_addr_by_compatible                           
if [ $? -ne 0 ]; then                                                                  
    exit 1                            
fi

case "$1" in
    startup)
        startup
        ;;
    version)
        get_version
        ;;
    reset)
        reset_board
        ;;
    bootloader)
        enter_bootloader
        ;;
    bootloader-exit)
        exit_bootloader
        ;;
    flash)
        flash_device "$2"
        ;;
    find)
        echo "I2C device: $I2C_DEV"
        echo "I2C address: $I2C_ADDR"
        ;;
    latest-firmware)
        latest_firmware
        ;;
    *)
        usage
        exit 1
        ;;
esac

exit 0
