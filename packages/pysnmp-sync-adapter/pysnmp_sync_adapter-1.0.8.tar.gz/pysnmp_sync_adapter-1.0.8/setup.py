#!/usr/bin/env python3
# -*- coding: utf-8 -*-
###########################################################################
# pysnmp-sync-adapter
# Lightweight Synchronous Adapter for PySNMP AsyncIO HLAPI
###########################################################################

from setuptools import setup, find_packages
import re
import os
import sys

import json
from urllib import request
from pkg_resources import parse_version

###########################################################################

END_OF_INTRODUCTION = '## Quick Start'

EPILOGUE = '''
Full information and usage details at the [pysnmp-sync-adapter GitHub repository](https://github.com/Ircama/pysnmp-sync-adapter).
'''

DESCRIPTION = ("Lightweight Synchronous wrapper adapters for PySNMP AsyncIO HLAPI")
PACKAGE_NAME = "pysnmp-sync-adapter"

VERSIONFILE = "pysnmp_sync_adapter/__version__.py"

###########################################################################

def versions(pkg_name, site):
    url = 'https://' + site + '.python.org/pypi/' + pkg_name + '/json'
    try:
        releases = json.loads(request.urlopen(url).read())['releases']
    except Exception as e:
        print("Error while getting data from URL '" + url + "': " + e)
        return []
    return sorted(releases, key=parse_version, reverse=True)

with open("README.md", "r") as readme:
    long_description = readme.read()

build = ''
verstrline = open(VERSIONFILE, "rt").read()
VSRE = r"^__version__ = ['\"]([^'\"]*)['\"]"
mo = re.search(VSRE, verstrline, re.M)
if mo:
    verstr = mo.group(1)
else:
    raise RuntimeError("Unable to find version string in %s." % (VERSIONFILE,))


setup(
    name=PACKAGE_NAME,
    version=verstr,
    description=(DESCRIPTION),
    long_description=long_description[
        :long_description.find(END_OF_INTRODUCTION)] + EPILOGUE,
    long_description_content_type="text/markdown",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
    ],
    keywords=("snmp synchronous pysnmp"),
    author="Ircama",
    project_urls={
        "Homepage": "https://github.com/Ircama/pysnmp-sync-adapter",
        "Repository": "https://github.com/Ircama/pysnmp-sync-adapter"
    },
    license="EUPL-1.2",
    packages=find_packages(),
    install_requires=["pysnmp>=7.0.0"],
    python_requires=">=3.7",
)
