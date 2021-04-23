# raspy
A personal, offline assistant using the vosk library for speech recognition

Software:\
Raspberry Pi OS Lite (32-bit), distributed on 2021-03-04

Hardware:\
Raspberry Pi 3 Modell B+ (with micro usb cable, casing and 16 gb sd card)\
Pirate Audio: Dual Mic for Raspberry Pi

How to set up:
1. git clone https://github.com/PelzKo/raspy.git
2. cd raspy
3. bash setup.sh
4. sudo crontab -e (add the line "@reboot sudo -u pi /home/pi/raspy/run.sh /home/pi/raspy >/home/pi/raspy/logs/cron.log 2>&1")
