#!/bin/bash

###### Pirate-audio microphone requirements ######
bash install_pirate_audio.sh


##### Required packages ######
pip3 install vosk
pip3 install requests
pip3 install pyttsx3
#pip3 install json

###### Create folder for log files ######
mkdir logs

###### Language model download ######
bash install_language_model.sh
