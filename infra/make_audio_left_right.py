import sys, os, glob
from pydub import AudioSegment
import pyogg

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

def make(filename):
    basename, ext = os.path.splitext(filename)
    dirname, basename = os.path.split(basename)
    if basename.endswith("_left") or basename.endswith("_right"):
        return

    print("Opening", filename)
    sound = AudioSegment.from_file(filename)
    print("  frame_rate:", sound.frame_rate, " count:", sound.frame_count())
    if sound.frame_rate != 44100:
        sound = sound.set_frame_rate(44100)

    sound_mono = sound.set_channels(1)
    #sound_mono.export(basename + "_mono" + ext)

    dur = sound_mono.duration_seconds*1000
    if sound_mono.frame_rate * (dur / 1000) != sound_mono.frame_count():
        dur += 0.0001  # stupid numerical error

    sil = AudioSegment.silent(duration=dur, frame_rate=sound_mono.frame_rate)
    assert sil.frame_count() == sound_mono.frame_count(), "frame_count mismatch"

    sound_left = AudioSegment.from_mono_audiosegments(sound_mono, sil)
    left_name = dirname + "/_" + basename + "_left.ogg"
    sound_left.export(left_name, format="ogg")

    sound_right = AudioSegment.from_mono_audiosegments(sil, sound_mono)
    right_name = dirname + "/_" + basename + "_right.ogg"
    sound_right.export(right_name, format="ogg")

   # v = pyogg.VorbisFile(left_name)
   # print(v)

def main(argv):
    for name in glob.glob(argv[1]):
        make(name)

if __name__ == "__main__":
    main(sys.argv)