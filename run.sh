#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

source "$DIR"/config.py

# shellcheck disable=SC2154
current_model="${DIR}/src/models/model_$language"
[ ! -d "$current_model" ] && bash "$DIR"/install_language_model.sh

# shellcheck disable=SC2154
python3 "$DIR"/src/main_listener.py --device "$device" --model_base "$DIR"/models --logs "$DIR"/logs
