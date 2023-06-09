# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:44:34 2023

@author: ISipila
"""

from setuptools import setup, find_packages

import os

def package_files(directory):
    paths = []
    for (path, directories, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join('..', path, filename))
    return paths

extra_files = package_files('LBLDataAccess/lookups')
config = package_files('LBLDataAccess/config')
all_files = extra_files + config

setup(
    name='LBLDataAccess',
    version='0.2.1',
    author='Ilkka Sipila',
    author_email='ilkka.sipila@lewisham.gov.uk',
    packages=find_packages(include=['LBLDataAccess', 'LBLDataAccess.*']),
    package_data={'LBLDataAccess': all_files},
    install_requires=[
        'requests',
        'pandas',
        'openpyxl',
    ],
)