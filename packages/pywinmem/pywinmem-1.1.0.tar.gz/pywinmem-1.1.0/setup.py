# pywinmem - Windows memory manipulation toolkit
# Copyright (C) 2025 fuckin_busy
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

from setuptools import setup, find_packages

with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="pywinmem",
    version="1.1.0",
    author="fuckin_busy",
    author_email="",
    description="Windows memory manipulation toolkit for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fuckin_busy/pywinmem",
    packages=find_packages(),
    package_data={
        "pywinmem.low": ["*.dll"],
    },
    install_requires=[],
    python_requires=">=3.10",
    license="GPL-3.0-or-later",
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Microsoft :: Windows",
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
    ],
    keywords=[
        "windows",
        "memory",
        "process",
        "ctypes",
        "reverse engineering",
        "game hacking"
    ],
    project_urls={
        "Source": "https://github.com/fuckin_busy/pywinmem",
    },
)
