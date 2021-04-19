#!/bin/bash

base=/home/pi/raspy
#echo $base
device_name="mic_out"
#sudo -u pi python3 $base/src/main_listener.py -d $device_name -m $base/model 2>> "$base/logs/$(date +'%Y%m%dT%H%M').err" 1>> "$base/logs/$(date +'%Y%m%dT%H%M').out"
python3 $base/src/main_listener.py --device $device_name --model $base/model --logs $base/logs
