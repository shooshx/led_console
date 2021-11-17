import os
from setuptools import Extension, setup
from Cython.Build import cythonize

this_dir = os.path.dirname(os.path.abspath(__file__))

extensions = [
    Extension("infra_c", ["infra_c.pyx"],
        libraries=["SDL2"],
        library_dirs=[this_dir + "/SDL2/lib/x64"],
        include_dirs=['/usr/include/SDL2',
                      this_dir + "/SDL2/include"]
    )
]

setup(
    name='Infra',
    ext_modules=cythonize(extensions, language_level="3"),
    zip_safe=False,
)

# sudo apt-get install -y build-essential tk-dev libncurses5-dev libncursesw5-dev libreadline6-dev libdb5.3-dev libgdbm-dev libsqlite3-dev libssl-dev libbz2-dev libexpat1-dev liblzma-dev zlib1g-dev libffi-dev

# sudo apt-get install libsdl2-dev python3-dev libsdl2-mixer-2.0-0 libatlas-base-dev
#   libatlast for numpy
# sudo pip3 install Pillow Cython pysdl2 pycairo scipy

#  python3 setup.py build_ext --inplace

