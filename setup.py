#!/usr/bin/python
from setuptools import setup, find_packages

setup(
    name = "az",
    version = "0.1",
    packages = find_packages(),
    scripts = ['telemetry.py'],
    install_requires = ['simplejson'],
)

