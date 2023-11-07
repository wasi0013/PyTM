#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from setuptools._distutils import setup


if sys.argv[-1] == "publish":
    os.system("python setup.py sdist upload")
    sys.exit()

readme = open("README.rst").read()
doclink = """
Documentation
-------------

The full documentation is at http://PyTM.rtfd.org."""
history = open("HISTORY.rst").read().replace(".. :changelog:", "")

setup(
    name="python-pytm",
    version="0.0.14",
    description="PyTM - an Open Source Python Time Management Tool for Mankind",
    long_description=readme + "\n\n" + doclink + "\n\n" + history,
    long_description_content_type="text/x-rst",
    author="Wasi",
    author_email="wasi0013@gmail.com",
    url="https://github.com/wasi0013/PyTM",
    packages=["PyTM", "PyTM.commands", "PyTM.core"],
    package_dir={"python-pytm": "PyTM"},
    include_package_data=True,
    install_requires=["click", "rich"],
    license="MIT",
    zip_safe=False,
    keywords="PyTM",
    entry_points={
        "console_scripts": ["pytm=PyTM.cli:cli"],
    },
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.12",
    ],
)
