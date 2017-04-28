#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from os.path import *


def read_requires(path=None):
    if path is None:
        path = join(dirname(__file__), 'requirements.txt')
        print(path)

    with open(path) as fp:
        return [l.strip() for l in fp.readlines()]


setup(**{
    'name': 'uspech',
    'version': '0.1.2',
    'author': 'Singularita s.r.o.',
    'description': 'Common project utilities (not for general use)',
    'license': 'MIT',
    'keywords': 'utilities',
    'url': 'http://github.com/singularita/uspech/',
    'include_package_data': True,
    'package_data': {
        '': ['*.png', '*.js', '*.html'],
    },
    'packages': find_packages(),
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
    ],
    'install_requires': read_requires(),
})


# vim:set sw=4 ts=4 et:
