# raspy
A personal, offline assistant using the vosk library for speech recognition

Software:\
Raspberry Pi OS Lite (32-bit), distributed on 2021-03-04

Hardware:\
Raspberry Pi 3 Modell B+ (with micro usb cable, casing and 16 gb sd card)\
Pirate Audio: Dual Mic for Raspberry Pi

Prerequisites (with "raspi-config"):
- Set the locale and time zone
- WiFi set up or LAN
- Autologin enabled

How to set up:
1. sudo apt update
2. sudo apt install git
3. git clone https://github.com/PelzKo/raspy.git
4. cd raspy
5. sudo -u pi bash setup.sh
6. sudo crontab -e (add the line "@reboot sudo -u pi bash /home/pi/raspy/run.sh >/home/pi/raspy/logs/cron.log 2>&1")


Example build (bought on the 04.04.2021 on https://www.berrybase.de/):

| Name (in german)                                                        | Product Id   | Price   |
| :---------------------------------------------------------------------: |:------------:| :------:|
| Raspberry Pi 3 Modell B+                                                | RPI3-BP      | 37,70 € |
| Micro USB Netzteil für Raspberry Pi 5V / 2,5A schwarz                   | 8012053      | 4,90 €  |
| Gehäuse für Raspberry Pi 3B+, 3B, 2B, 1B+ schwarz                       | 1677046      | 4,50 €  |
| SanDisk Ultra microSDHC A1 98MB/s Class 10 Speicherkarte + Adapter 16GB | 619659161347 | 4,90 €  |
| Pirate Audio HAT für Raspberry Pi, für Stereoaufnahmen                  | PIRATE-5     | 26,67 € |


Current functionality:
- Writing notes through telegram
- Giving the weather for Innsbruck
- Random number generator
- Flipping a coin
- Setting a timer
- Rebooting and shutting down
- Changing the language between german and englisch