# raspy
A personal, offline assistant using the vosk library for speech recognition

Software:\
Raspberry Pi OS Lite (32-bit), distributed on 2021-03-04

Hardware:\
Raspberry Pi 3 Modell B+ (with micro usb cable, casing and 16 gb sd card)\
Pirate Audio: Dual Mic for Raspberry Pi

Prerequisites (with "raspi-config"):
- Set the locale and time zone
- WiFi set up
- Autologin enabled

How to set up:
1. sudo apt update
2. sudo apt install git
3. git clone https://github.com/PelzKo/raspy.git
4. cd raspy
5. bash setup.sh
6. sudo crontab -e (add the line "@reboot sudo -u pi /home/pi/raspy/run.sh >/home/pi/raspy/logs/cron.log 2>&1")
