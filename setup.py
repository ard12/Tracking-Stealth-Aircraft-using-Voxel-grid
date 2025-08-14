# setup.py
# This script compiles the C++ extension module `projector_core.cpp` using pybind11.
# To build the module, run: python setup.py install

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
import pybind11
import sys

class BuildExt(build_ext):
    """A custom build extension for adding compiler-specific options."""
    c_opts = {
        'msvc': ['/EHsc', '/O2', '/openmp'],
        'unix': ['-O3', '-fopenmp', '-std=c++17'],
    }
    l_opts = {
        'msvc': [],
        'unix': ['-fopenmp'],
    }

    def build_extensions(self):
        ct = self.compiler.compiler_type
        opts = self.c_opts.get(ct, [])
        link_opts = self.l_opts.get(ct, [])
        if ct == 'unix':
            opts.append(f'-DVERSION_INFO="{self.distribution.get_version()}"')
        elif ct == 'msvc':
            opts.append(f'/DVERSION_INFO=\\"{self.distribution.get_version()}\\"')

        for ext in self.extensions:
            ext.extra_compile_args = opts
            ext.extra_link_args = link_opts
        
        build_ext.build_extensions(self)

ext_modules = [
    Extension(
        # The name of the module in Python
        'projector_core', 
        # The source file
        ['projector_core.cpp'],
        include_dirs=[
            # Path to pybind11 headers
            pybind11.get_include(),
        ],
        language='c++'
    ),
]

setup(
    name='projector_core',
    version='0.0.1',
    author='Your Name',
    author_email='your.email@example.com',
    description='C++ accelerated module for 3D voxel projection',
    ext_modules=ext_modules,
    cmdclass={'build_ext': BuildExt},
    zip_safe=False,
)
