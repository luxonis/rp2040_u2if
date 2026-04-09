#!/bin/bash

# this runs on the device
if [ -z "$1" ]; then
    echo "Usage: $0 <can image>"
    exit 1
fi
can_image=$1

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

flash_can() {
    image=$1

    while true; do
        # put CAN stm into bootloader mode
        echo "Putting CAN into bootloader mode"
        python set_prog_state_can.py 0
        
        sleep 2

        # find STM DFU bootloader
        find_usb_device "0483" "df11"
        if [ $? -ne 0 ]; then
            echo "No STM DFU bootloader found"

            echo "Replug the power cable and try again"
            read -n 1 -s
            continue
        fi

        echo "Found STM DFU bootloader"
        echo "Flashing CAN"
        dfu-util -a 0 -i 0 -s 0x08000000:leave -D $image

        sleep 2
        python set_prog_state_can.py 1
        sleep 2
        
        # find CAN device OpenMoko VID
        find_usb_device "1d50" "606f"
        if [ $? -ne 0 ]; then
            echo "No CAN found"

            echo "Replug the power cable and try again"
            read -n 1 -s
            continue
        fi

        echo "CAN flashed successfully"

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

flash_can $can_image
if [ $? -ne 0 ]; then
    echo "CAN flash failed"
    exit 1
fi