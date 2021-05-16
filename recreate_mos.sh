#!/bin/bash

cd locales/de/LC_MESSAGES
../../../msgfmt.py -o base.mo base
cd ../../
cd en/LC_MESSAGES
../../../msgfmt.py -o base.mo base