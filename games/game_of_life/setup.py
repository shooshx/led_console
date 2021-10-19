

from setuptools import setup
from Cython.Build import cythonize

setup(
    name='Hello world app',
    ext_modules=cythonize("game_of_life.pyx", language_level="3"),
    zip_safe=False,
)


#  python setup.py build_ext --inplace