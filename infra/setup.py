import sys, os
from setuptools import Extension, setup
from Cython.Build import cythonize
import setup_helper

this_dir = os.path.dirname(os.path.abspath(__file__))

rpi_rgb_led_matrix_dir = "/home/pi/adafruit/rpi-rgb-led-matrix"

libs = ["SDL2"]
if sys.platform == "linux":
    lib_dirs = [ rpi_rgb_led_matrix_dir + '/lib' ]
    inc_dirs = [ '/usr/include/SDL2',
                 rpi_rgb_led_matrix_dir + '/include'
               ]
    libs.append("rgbmatrix")
    cflags =  ["-O3", "-g0", "-s"]
else:
    lib_dirs = [ this_dir + "/SDL2/lib/x64" ]
    inc_dirs = [ this_dir + "/SDL2/include" ]
    cflags = []    

extensions = [
    Extension("infra_c", ["infra_c.pyx"],
        libraries =libs,
        library_dirs = lib_dirs,
        include_dirs = inc_dirs,
        language = 'c++',
        extra_compile_args = cflags
    )
]



setup(
    name='Infra',
    ext_modules=cythonize(extensions, language_level="3" ),
    zip_safe=False,
    cmdclass=setup_helper.CMDCLASS,
)

# sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev

# sudo apt-get install libsdl2-dev python3-dev libsdl2-mixer-2.0-0 libatlas-base-dev
#   libatlast for numpy
# sudo pip3 install Pillow Cython pysdl2 pycairo scipy

#  python3 setup.py build_ext --inplace

