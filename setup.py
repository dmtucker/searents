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

setup(
    name='searents',
    version='0.12.4',
    description='A Scraper of Seattle Rents',
    long_description=README,
    author='David Tucker',
    author_email='david@tucker.name',
    license='LGPLv2+',
    url='https://gitlab.com/dmtucker/searents',
    packages=find_packages(),
    include_package_data=True,
    python_requires='~=3.6',
    install_requires=[
        'fake_useragent~=0.1.0',
        'python-dateutil~=2.6.0',
        'requests~=2.9.1',
    ],
    extras_require={
        'visualizer': [
            'matplotlib~=2.2.3',
        ],
    },
    entry_points={
        'console_scripts': [
            'searents = searents.cli:main',
            'searents-parse = searents.parse:main',
        ],
    },
    keywords='rent scraper',
    classifiers=[
        'License :: OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)',
        'Intended Audience :: End Users/Desktop',
        'Development Status :: 4 - Beta',
    ],
)
