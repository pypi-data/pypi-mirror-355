#!/usr/bin/python3

import codecs
import os
import re

from setuptools import setup, find_packages

long_description = """tbd"""

requires = [
    'ply',
]

__name__ = 'norpm'
__description__ = "tbd"
__author__ = "Pavel Raiskup"
__author_email__ = "pavel@raiskpu.cz"
__url__ = "https://github.com/praiskup/norpm"


setup(
    name=__name__,
    version="0.0",
    description=__description__,
    long_description=long_description,
    author=__author__,
    author_email=__author_email__,
    url=__url__,
    license='LGPLv2+',
    install_requires=requires,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'copr-cli = copr_cli.main:main'
        ]
    },
)
