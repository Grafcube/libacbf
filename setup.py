#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name="libacbf",
      version='1.0.0',
      description="A library to read and edit ACBF formatted comic book files and archives.",
      author="Grafcube",
      license="BSD-3-Clause License",
      url="https://github.com/Grafcube/libacbf",
      packages=find_packages(include=["libacbf"]),
      setup_requires=["pytest-runner"],
      tests_require=["pytest"],
      test_suite="tests",
      download_url="",  # TODO: After docs
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
          ]
      )
