#!/bin/bash

base=$1
[[ -z "$base" ]] && { echo "Error: No base directory supplied"; exit 1; }
source "$base"/config.py

# shellcheck disable=SC2154
current_model="src/models/model_$language"
[ ! -d "$current_model" ] && bash "$base"/install_language_model.sh

# shellcheck disable=SC2154
python3 "$base"/src/main_listener.py --device "$device" --model_base "$base"/models --logs "$base"/logs
