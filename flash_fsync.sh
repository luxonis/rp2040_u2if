#!/bin/bash

# this runs on the device
if [ -z "$1" ]; then
    echo "Usage: $0 <fsync image>"
    exit 1
fi
fsync_image=$1

flash_fsync() {
    image=$1

    while true; do
        # ask the user to attach i2c probes to i2c lines and wait for input
        echo "Attach i2c probes to i2c lines and press ENTER..."
        read -n 1 -s

        echo "Flashing FSYNC"

        ./program-fsync-controller-m8-box.sh flash $image

        if [ $? -ne 0 ]; then
            echo "FSYNC flash failed, retrying..."
            continue
        fi
    
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

# enable i2c on m8 connector
echo "Enabling i2c on m8 connector"
gpioset 0 124=0 79=0

flash_fsync $fsync_image
if [ $? -ne 0 ]; then
    echo "FSYNC flash failed"
    exit 1
fi