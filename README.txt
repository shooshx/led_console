
pip install PySDL27
pip install pysdl2-dll

from: https://github.com/hzeller/rpi-rgb-led-matrix/
  sudo apt-get remove bluez bluez-firmware pi-bluetooth triggerhappy pigpio

sudo systemctl stop cron
sudo systemctl stop nmbd
sudo systemctl stop smbd

Audio from USB:
https://www.raspberrypi-spy.co.uk/2019/06/using-a-usb-audio-device-with-the-raspberry-pi/

sudo nano /usr/share/alsa/alsa.conf
  defaults.ctl.card 1
  defaults.pcm.card 1


change resolution:
    sudo raspi-config

alsamixer -c 1
speaker-test
aplay -l
arecord

led matrix install:
https://learn.adafruit.com/adafruit-rgb-matrix-bonnet-for-raspberry-pi/driving-matrices

sudo ./demo -D3 --led-rows=32 --led-cols=32 --led-chain=2 --led-multiplexing=1 --led-brightness=50

sudo ./demo -D4 --led-rows=64 --led-cols=64 --led-chain=4 --led-multiplexing=1 --led-brightness=20 --led-slowdown-gpio=4

sudo ./demo -D4 --led-rows=64 --led-cols=64 --led-chain=4 --led-multiplexing=1 --led-brightness=40 --led-slowdown-gpio=2 --led-show-refresh --led-limit-refresh 60


images:
https://loading.io/

sounds:
https://artlist.io/sfx/pack/2088/retro-games
http://sonniss.com/gameaudiogdc#1605030813191-c5a1f3d0-8baf
https://www.epidemicsound.com/

G4F SFX05
Gamemaster Audio - Retro 8Bit Sounds

opencl:
https://qengineering.eu/install-opencl-on-raspberry-pi-3.html

pico commands
    keyconfig

wifi:
    sudo raspi-config
    sudo ip link set wlan0 up
    sudo ip link set wlan0 down
    iwconfig
    sudo iwlist wlan0 scan
    sudo nano /etc/wpa_supplicant/wpa_supplicant.conf

retro-pie startup
    /etc/profile.d/10-retropie.sh
    /opt/retropie/configs/all/autostart.sh
    emulationstation

low power
    vcgencmd get_throttled

