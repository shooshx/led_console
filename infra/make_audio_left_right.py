import sys, os
from pydub import AudioSegment

# set PATH=%PATH%;C:\utils\ffmpeg-N-104465-g08a501946f-win64-lgpl\bin

def main_with_pan(argv):
    filename = argv[1]
    sound1 = AudioSegment.from_file(filename)

    basename, ext = os.path.splitext(filename)
    # pan the sound 15% to the right
    panned_right = sound1.pan(+1.0)
    panned_right.export(basename + "_right" + ext)

    # pan the sound 50% to the left
    panned_left = sound1.pan(-1.0)
    panned_left.export(basename + "_left" + ext)

def main(argv):
    filename = argv[1]
    sound = AudioSegment.from_file(filename)

    basename, ext = os.path.splitext(filename)

    sound_mono = sound.set_channels(1)
    #sound_mono.export(basename + "_mono" + ext)

    sil = AudioSegment.silent(duration=sound_mono.duration_seconds*1000, frame_rate=sound_mono.frame_rate)

    sound_left = AudioSegment.from_mono_audiosegments(sound_mono, sil)
    sound_left.export(basename + "_left" + ext)

    sound_right = AudioSegment.from_mono_audiosegments(sil, sound_mono)
    sound_right.export(basename + "_right" + ext)

if __name__ == "__main__":
    main(sys.argv)