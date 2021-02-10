import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent
README = (HERE / "README.mess").read_text()

setup(
    name='pylichat',
    version='1.1',
    description='A library for the Lichat protocol',
    long_description=README,
    license='zlib',
    author='Nicolas Hafner',
    author_email='shinmera@tymoon.eu',
    keywords=['chat','protocol'],
    url='https://github.com/shirakumo/py-lichat',
    packages=['pylichat'],
    classifiers=[
        "License :: OSI Approved :: zlib/libpng License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Internet"
    ],
    entry_points={
        "console_scripts": [
            "pylichat=pylichat.__main__:main",
        ]
    },
)
