#!/bin/bash


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

###### Pirate-audio microphone requirements ######
bash "$DIR"/install_pirate_audio.sh


##### Required packages ######
pip3 install vosk
pip3 install requests
pip3 install pyttsx3

###### Create folder for log files ######
mkdir -p "$DIR"/logs

###### Language model download ######
bash "$DIR"/install_language_model.sh
