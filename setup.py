#!/usr/bin/env python

import sys
from setuptools import setup, find_packages

version = "1.0.2"
version_config = {"version_config": True}
if sys.argv[1] == "version":
    version += sys.argv[2]
    version_config.clear()
    del sys.argv[2]
    del sys.argv[1]

with open("README.md", 'r', encoding="utf-8") as readme:
    long_description = readme.read().strip()

setup(name="libacbf",
      version=version,
      description="A library to read and edit ACBF formatted comic book files and archives.",
      long_description=long_description,
      long_description_content_type='text/markdown',
      author="Grafcube",
      license="BSD-3-Clause License",
      url="https://github.com/Grafcube/libacbf",
      packages=find_packages(include=["libacbf"]),
      include_package_data=True,
      setup_requires=["pytest-runner", "setuptools-git-versioning"],
      tests_require=["pytest"],
      test_suite="tests",
      download_url="https://pypi.org/project/libacbf/",
      keywords=[
          "python",
          "library",
          "book",
          "comic",
          "ebook",
          "comics",
          "python3",
          "ebooks",
          "acbf"
          ],
      install_requires=[
          "wheel",
          "lxml",
          "python-magic",
          "py7zr",
          "rarfile",
          "requests",
          "langcodes",
          "python-dateutil"
          ],
      classifiers=[
          "Development Status :: 5 - Production/Stable",
          "License :: OSI Approved :: BSD License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3 :: Only",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "Topic :: Software Development :: Libraries",
          "Typing :: Typed"
          ],
      **version_config
      )
