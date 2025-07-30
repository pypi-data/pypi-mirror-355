from setuptools import setup
from Cython.Build import cythonize

setup(
    name="helloworldcy",
    version="0.1.7",
    packages=["helloworldcy"],
    ext_modules=cythonize("helloworldcy/hello.pyx"),
    zip_safe=False,
)