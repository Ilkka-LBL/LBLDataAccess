# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 10:44:34 2023

@author: ISipila
"""

from setuptools import setup, find_packages

setup(
    name='LBLDataAccess',
    version='0.1.0',
    author='Ilkka Sipila',
    author_email='ilkka.sipila@lewisham.gov.uk',
    packages=find_packages(include=['LBLDataAccess', 'LBLDataAccess.*']),
    package_data={'LBLDataAccess': ['config/config.json', 'lookups/*', 'lookups/*/*.csv', 'lookups/*/*.xlsx']},
    install_requires=[
        'requests',
        'pandas',
    ],
)