#!/bin/bash

# this runs on the device
set -e

if [ -z "$1" || -z "$2" || -z "$3" ]; then
    echo "Usage: $0 <rpi image> <can image> <fsync image>"
    exit 1
fi
rpi_image=$1
can_image=$2
fsync_image=$3

find_usb_device() {
    vendor_id=$1
    product_id=$2

    echo "Looking for USB device with vendor_id=$vendor_id and product_id=$product_id"

    usb_dev=$(lsusb | grep -E "^Bus[[:space:]]+?[0-9]{3}[[:space:]]+?Device[[:space:]]+?[0-9]{3}:[[:space:]]+?ID[[:space:]]+?$vendor_id:$product_id.*?$")

    if [ -z "$usb_dev" ]; then
        echo "No device found."
        exit 1
    fi
    echo "Found device: $usb_dev"
    exit 0
}

flash_rpi() {
    image=$1

    while true; do
        while true; do
            # ask user to boot rp2040 into bootloader and wait for input
            echo "Press the boot button while powering the m8 box"
            read -n 1 -s

            # check if rpi presents as a storage device
            disk_dev=$(lsblk -o NAME,MODEL,VENDOR | grep -E "^sd[a-z][[:space:]]+?RP2[[:space:]]+?RPI.*?$")
            ret=$?
            if [ $ret -ne 0 ]; then
                echo "No disk found, retrying..."
                continue
            fi

            # get disk device name
            disk_dev=$(echo $disk_dev | sed -E "s/^(sd[a-z])[[:space:]]+?RP2[[:space:]]+?RPI.*?$/\1/")

            part_dev=$(ls /dev/"$disk_dev"1)
            ret=$?
            if [ $ret -ne 0 ]; then
                echo "No partition found, retrying..."
                continue
            fi

            echo "Found disk: $part_dev"

            break
        done

        if [ -z "$part_dev" ]; then
            echo "No disk found"
            exit 1
        fi

        echo "Mounting disk $part_dev"
        mkdir -p mnt
        mount $part_dev mnt

        echo "Copying RPI image to disk"
        cp $image mnt/

        echo "waiting for RPI to boot"
        sleep 7

        umount mnt

        # check if rpi booted correctly
        find_usb_device "cafe" "4005"
        if [ $? -ne 0 ]; then
            echo "No RPI found, retrying..."
            continue
        fi

        echo "RPI flashed successfully"

        break
    done
    exit 0
}

flash_can() {
    image=$1

    # put CAN stm into bootloader mode
    echo "Putting CAN into bootloader mode"
    python set_prog_state_can.py 0
    
    sleep 2

    # find STM DFU bootloader
    find_usb_device "0483" "df11"
    if [ $? -ne 0 ]; then
        echo "No STM DFU bootloader found"
        exit 1
    fi

    echo "Found STM DFU bootloader"
    echo "Flashing CAN"
    dfu-util -a 0 -i 0 -s 0x08000000:leave -D candleLight_fw.bin
    
    # find CAN device OpenMoko VID
    find_usb_device "1d50" "606f"
    if [ $? -ne 0 ]; then
        echo "No CAN found"
        exit 1
    fi

    echo "CAN flashed successfully"

    exit 0
}

flash_fsync() {
    image=$1

    # ask the user to attach i2c probes to i2c lines and wait for input
    echo "Attach i2c probes to i2c lines"
    read -n 1 -s

    echo "Flashing FSYNC"

    ./program-fsync-controller-m8-box.sh flash $image

    if [ $? -ne 0 ]; then
        echo "FSYNC flash failed"
        exit 1
    fi

    exit 0
}

# check if directory exists
if [ ! -d ./venv/ ]; then
    python3 -m venv venv
fi

# activate virtual environment
echo "Activating virtual environment"
source venv/bin/activate

test_pip=$(pip -v)
if [ $? -ne 0 ]; then
    python3 -m ensurepip
fi
pip install -r requirements.txt

# enable m8 usb
echo "Enabling m8 usb"
gpioset 0 32=0
echo host > /sys/class/usb_role/a600000.ssusb-role-switch/role

flash_rpi $rpi_image
if [ $? -ne 0 ]; then
    echo "RPI flash failed"
    exit 1
fi

flash_can $can_image
if [ $? -ne 0 ]; then
    echo "CAN flash failed"
    exit 1
fi

flash_fsync $fsync_image
if [ $? -ne 0 ]; then
    echo "FSYNC flash failed"
    exit 1
fi