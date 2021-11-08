import sys, os
import PIL.Image


# process of creating these
# - create animation in flash
# - export from flash to image sequence
# - open as image sequence in photoshop
# -   motion workspace in photoshop to see it
# - export to web in photoshop


def main(argv):
    template = argv[1]
    i = 0
    imgs = []
    width = None
    height = None
    while True:
        name = template.format(i)
        exist = os.path.exists(name)
        if not exist and i > 0:
            break
        i += 1
        if not exist:
            continue
        print("opening", name)
        img = PIL.Image.open(name)
        if width is None:
            width = img.width
            height = img.height
        else:
            assert width == img.width and height == img.height
        imgs.append(img)

    seq = PIL.Image.new('RGBA', (width, height*len(imgs)))
    for i,im in enumerate(imgs):
        seq.paste(im, (0, height*i))
    seq.save(argv[2])
    print("saved")


# example "balls{:02d}.png"
#  C:\Projects\led_console\games\pong\balls_anim3\test_3{:04d}.png

if __name__ == "__main__":
    main(sys.argv)