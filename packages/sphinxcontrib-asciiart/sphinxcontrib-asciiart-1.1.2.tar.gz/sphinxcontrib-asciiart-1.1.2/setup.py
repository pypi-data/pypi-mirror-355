#!/usr/bin/env python3
from setuptools import setup, find_packages

requires = ['Sphinx>=1.0b2']

setup(name='sphinxcontrib-asciiart',
    version='1.1.2',
    url='https://pypi.org/project/sphinxcontrib-asciiart/',
    license='BSD',
    author='Yongping Guo',
    author_email='guoyoooping@163.com',
    description='Sphinx extension asciiart',
    long_description=open('README.rst').read(),
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
    namespace_packages=['sphinxcontrib'],
)
