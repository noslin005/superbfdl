#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup
import os
import re

__PATH__ = os.path.abspath(os.path.dirname(__file__))


def read_readme():
    with open('README.md') as f:
        return f.read()


def read_version():
    __PATH__ = os.path.abspath(os.path.dirname(__file__))
    with open(os.path.join(__PATH__, 'superbfdl/__init__.py')) as f:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  f.read(), re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find __version__ string")


__version__ = read_version()

install_requires = [
    'bs4>=0.0.1',
    'requests>=2.25.1',
]

setup(
    name='superbfdl',
    version=__version__,
    license='MIT',
    description='Utility to download BIOS and IPMI from Supermicro',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/noslin005/superbfdl',
    author='Nilson Lopes',
    author_email='nlopes@sourcecode.com',
    keywords='bios ipmi bmc supermicro download',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Topic :: System :: Firmware',
    ],
    package=['superbfdl'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': ['superbfdl=superbfdl:main'],
    },
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.4',
)
