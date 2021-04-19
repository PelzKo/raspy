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

###### Vosk installation ######
#cd src || exit 2
wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
rm vosk-model-small-en-us-0.15.zip
