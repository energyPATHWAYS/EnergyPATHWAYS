from distutils.core import setup
from Cython.Build import cythonize
import numpy

setup(ext_modules=cythonize("rollover_c.pyx"),
      include_dirs=[numpy.get_include()])

# python rollover_c_setup.py build_ext --inplace
