#!/usr/bin/python
from setuptools import setup, find_packages

setup(
    name = "az",
    version = "0.1",
    packages = ['az', 'az.proto', 'az.plugins_available', 'az.plugins_enabled'],
    scripts = ['telemetry.py'],
    install_requires = ['simplejson', 'gnupg', 'protobuf'],
)
