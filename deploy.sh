#!/bin/bash

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <device ip>"
    exit 1
fi

DEVICE_IP=$1

echo "Deploying to $DEVICE_IP"

mkdir -p deploy_m8
cp -r src deploy_m8
cp candleLight_fw.bin deploy_m8
cp u2if_MD6976_R0.uf2 deploy_m8
cp program-fsync-controller-m8-box.sh deploy_m8
cp requirements.txt deploy_m8
cp set_prog_state_can.py deploy_m8
cp set_prog_state.py deploy_m8
cp flash_m8_box.sh deploy_m8

zip -r m8_flashing.zip deploy_m8
scp m8_flashing.zip root@$DEVICE_IP:/data/m8_flashing.zip
ssh root@$DEVICE_IP "cd /data && unzip m8_flashing.zip && rm m8_flashing.zip"
rm -rf deploy_m8
rm m8_flashing.zip
