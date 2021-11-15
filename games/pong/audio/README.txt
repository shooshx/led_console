PATH=%PATH%;C:\utils\ffmpeg-N-104465-g08a501946f-win64-lgpl\bin

python ..\..\..\infra\make_audio_left_right.py pop\pop*
python ..\..\..\infra\make_audio_left_right.py hit\hit*
python ..\..\..\infra\make_audio_left_right.py crash\crash*