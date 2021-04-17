#!/bin/bash

###### Pirate-audio microphone requirements ######
bash install_pirate_audio.sh


##### Required packages ######
pip3 install vosk
pip3 install requests
#pip3 install json


###### Vosk installation ######
cd src
wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
