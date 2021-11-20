import sys, os
from setuptools import Extension, setup
from Cython.Build import cythonize

this_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.append(os.path.join(this_dir, "..", "..", "infra"))
import setup_helper

infra_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "infra")


if sys.platform == "linux":
    cflags = ["-O3", "-g0"]
else:
    cflags = []

extensions = [
    Extension("game_of_life", ["game_of_life.pyx"],
        language = 'c++',
        extra_compile_args = cflags
    )
]

setup(
    name='game_of_life',
    ext_modules=cythonize(extensions, language_level="3", include_path=[infra_dir]),
    zip_safe=False,
    cmdclass=setup_helper.CMDCLASS,
)


#  python3 setup.py build_ext --inplace