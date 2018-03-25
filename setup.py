#!/usr/bin/env python3

from setuptools import setup, find_packages
setup(
    name="Verbula",
    version="0.1",
    packages=find_packages(),
    scripts=['src/verbula.py'],

    install_requires=['unidecode>=1.0.0'],

    author="Emiel Wiedijk",
    author_email="me@aimileus.nl",
    description="Script to help you study your vocabulary",
    license="GPL3+"
)