#!/usr/bin/env python3
# coding: utf-8

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    README = readme_file.read()

with open('requirements.txt') as requirements_file:
    REQUIREMENTS = requirements_file.read().splitlines()

setup(
    name='searents',
    version='0.12.1',
    description='A Scraper of Seattle Rents',
    long_description=README,
    author='David Tucker',
    author_email='david@tucker.name',
    license='LGPLv2+',
    url='https://gitlab.com/dmtucker/searents',
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQUIREMENTS,
    entry_points={
        'console_scripts': [
            'searents = searents.cli:main',
            'searents-parse = searents.parse:main',
        ],
    },
    keywords='rent scraper',
    classifiers=[
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Development Status :: 4 - Beta',
    ],
)
