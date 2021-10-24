
import os
from setuptools import setup
from Cython.Build import cythonize

infra_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra")


setup(
    name='Hello world app',
    ext_modules=cythonize("game_of_life.pyx", language_level="3", include_path=[infra_dir]),
    zip_safe=False,
)


#  python setup.py build_ext --inplace