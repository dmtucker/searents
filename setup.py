#!/usr/bin/env python3
# coding: utf-8

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    README = readme_file.read()

setup(
    name="searents",
    use_scm_version=True,
    description="A Scraper of Seattle Rents",
    long_description=README,
    long_description_content_type="text/x-rst",
    author="David Tucker",
    author_email="david@tucker.name",
    license="LGPLv2+",
    url="https://gitlab.com/dmtucker/searents",
    package_dir={"": "src"},
    packages=find_packages("src"),
    include_package_data=True,
    python_requires=">=3.6",
    setup_requires=["setuptools_scm >= 4.1"],
    install_requires=[
        "fake_useragent>=0.1",
        "python-dateutil>=2.6",
        "requests>=2.20",
    ],
    extras_require={
        "visualizer": [
            "matplotlib>=2.2",
        ],
    },
    entry_points={
        "console_scripts": [
            "searents = searents.cli:main",
            "searents-parse = searents.parse:main",
        ],
    },
    keywords="rent scraper",
    classifiers=[
        "License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
        "Intended Audience :: End Users/Desktop",
        "Development Status :: 4 - Beta",
    ],
)
