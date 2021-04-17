#!/bin/bash

base=$PWD/src
device_name="mic_out"
python3 $base/main_listener.py -d $device_name -m $base/model 2> "$(date +"%Y%m%dT%H%M").err" 1> "$(date +"%Y%m%dT%H%M").out"