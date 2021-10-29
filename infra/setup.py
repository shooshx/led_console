import os
from setuptools import Extension, setup
from Cython.Build import cythonize

this_dir = os.path.dirname(os.path.abspath(__file__))

extensions = [
    Extension("infra_c", ["infra_c.pyx"],
        libraries=["SDL2"],
        library_dirs=[this_dir + "/SDL2/lib/x64"]
    )
]

setup(
    name='Infra',
    ext_modules=cythonize(extensions, language_level="3"),
    zip_safe=False,
)


#  python setup.py build_ext --inplace