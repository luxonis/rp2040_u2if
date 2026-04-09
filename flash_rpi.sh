#!/bin/bash

# this runs on the device
if [ -z "$1" ]; then
    echo "Usage: $0 <rpi image>"
    exit 1
fi
rpi_image=$1

find_usb_device() {
    vendor_id=$1
    product_id=$2

    echo "Looking for USB device with vendor_id=$vendor_id and product_id=$product_id"

    usb_dev=$(lsusb | grep -E "^Bus[[:space:]]+?[0-9]{3}[[:space:]]+?Device[[:space:]]+?[0-9]{3}:[[:space:]]+?ID[[:space:]]+?$vendor_id:$product_id.*?$")

    if [ -z "$usb_dev" ]; then
        echo "No device found."
        return 1
    fi
    echo "Found device: $usb_dev"
    return 0
}

flash_rpi() {
    image=$1

    while true; do
        while true; do
            # ask user to boot rp2040 into bootloader and wait for input
            echo "Press the boot button while powering the m8 box and press ENTER"
            read -n 1 -s
            echo "Discovering bootloader disk..."

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
            return 1
        fi

        echo "Mounting disk $part_dev"
        mkdir -p mnt
        mount $part_dev mnt

        echo "Copying RPI image to disk"
        cp $image mnt/

        echo "waiting for RPI to boot"
        sleep 10

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
    return 0
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

has_hidapi=$(pip freeze | grep hidapi)
ret=$?
if [ $ret -ne 0 ]; then
    python -m pip install -r requirements.txt
fi

# enable m8 usb
echo "Enabling m8 usb"
gpioset 0 32=0
echo none > /sys/class/usb_role/a600000.ssusb-role-switch/role
echo host > /sys/class/usb_role/a600000.ssusb-role-switch/role

flash_rpi $rpi_image
if [ $? -ne 0 ]; then
    echo "RPI flash failed"
    exit 1
fi