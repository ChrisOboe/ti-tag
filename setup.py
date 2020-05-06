#!/usr/bin/env python

from setuptools import setup


def readme():
    with open('README.md') as f:
        return f.read()

setup(
    name='ti-tag',
    version='0.0.1',
    author='Chris Oboe',
    author_email='chrisoboe@eml.cc',
    description='A library for tagging audio files with the data from tidal',
    license='GPLv3+',
    url='https://github.com/ChrisOboe/ti-tag',
    download_url='https://github.com/ChrisOboe/ti-tag/archive/0.0.1.tar.gz',
    packages=['ti-tag'],
    install_requires=[
    ],
    classifiers = [
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)"
    ],
)
