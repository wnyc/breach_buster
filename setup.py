#!/usr/bin/env python

"""
breach_buster
=================

Replacement for Django's gzip middleware.  Protects against BREACH.

"""

from setuptools import setup

setup(
    name='breach_buster_middleware',
    version='0.0.0',
    author='Adam DePrince',
    author_email='adeprince@nypublicradio.org',
    description='BREACH resistant gzip middleware',
    url="",
    long_description=__doc__,
    py_modules=[
        'breach_buster/__init__',
        'breach_buster/middleware/__init__',
        'breach_buster/middleware/gzip',
        ],
    packages=['breach_buster',],
    zip_safe=True,
    license='GPLv3',
    include_package_data=True,
    classifiers=[],
    scripts=[],
    install_requires=[
        'django',
        ]
    )
