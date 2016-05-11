#!/usr/bin/env python3
# coding: utf-8

"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup, find_packages
import searents

with open('README.rst') as readme_file:
    README = readme_file.read()

setup(
    name='searents',
    version=searents.__version__,
    description=searents.__doc__,
    long_description=README,
    author='David Tucker',
    author_email='david.michael.tucker@gmail.com',
    license='LGPLv2+',
    url='https://github.com/dmtucker/searents',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    include_package_data=True,
    entry_points={'console_scripts': ['searents = searents.__main__:main']},
    keywords='rent scraper',
    classifiers=[
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'Development Status :: 3 - Alpha',
    ],
)