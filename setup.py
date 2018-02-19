#!/usr/bin/python3 -tt
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


name = 'uspech'
version = '0.3.2'


def read_requires(path=None):
    from os.path import dirname, join

    if path is None:
        path = join(dirname(__file__), 'requirements.txt')
        print(path)

    with open(path) as fp:
        return [l.strip() for l in fp.readlines()]


cmdclass = {}

try:
    from sphinx.setup_command import BuildDoc
    cmdclass['build_sphinx'] = BuildDoc

except ImportError:
    print('WARNING: Sphinx not available, build_sphinx disabled.')


setup(**{
    'name': name,
    'version': version,
    'author': 'Singularita s.r.o.',
    'description': 'Common project utilities (not for general use)',
    'license': 'MIT',
    'keywords': 'utilities',
    'url': 'http://github.com/singularita/uspech/',
    'include_package_data': True,
    'zip_safe': False,
    'packages': find_packages(),
    'classifiers': [
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Developers',
    ],
    'install_requires': read_requires(),
    'cmdclass': cmdclass,
    'command_options': {
        'build_sphinx': {
            'project': ('setup.py', name),
            'version': ('setup.py', version),
            'release': ('setup.py', version),
        },
    },
})


# vim:set sw=4 ts=4 et:
