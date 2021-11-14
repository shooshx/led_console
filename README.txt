
pip install PySDL27
pip install pysdl2-dll


Audio from USB:
https://www.raspberrypi-spy.co.uk/2019/06/using-a-usb-audio-device-with-the-raspberry-pi/

sudo nano /usr/share/alsa/alsa.conf
  defaults.ctl.card 1
  defaults.pcm.card 1

alsamixer -c 1
speaker-test
aplay -l
arecord



images:
https://loading.io/

sounds:
https://artlist.io/sfx/pack/2088/retro-games
http://sonniss.com/gameaudiogdc#1605030813191-c5a1f3d0-8baf
G4F SFX05
Gamemaster Audio - Retro 8Bit Sounds