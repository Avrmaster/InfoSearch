from distutils.core import setup
from Cython.Build import cythonize
import numpy


setup(
    ext_modules=cythonize(["optimized/collections.pyx", "optimized/dictionary.pyx", "optimized/trie.pyx"]),
    include_dirs=[numpy.get_include()]
)
