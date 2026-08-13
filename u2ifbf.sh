#!/bin/bash

./deploy.sh $1
ssh root@$1 /data/deploy_m8/flash_rpi.sh /data/deploy_m8/u2if_MD6976.uf2
