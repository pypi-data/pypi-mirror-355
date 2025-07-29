# -*- coding: utf-8 -*-
"""
Setup script of ppgnss
"""

from setuptools import setup, find_packages

# python3 setup.py sdist bdist_wheel
# python3 -m twine upload dist/*
# python3 -m twine upload --repository testpypi dist/* # testpypi

setup(
    name='ppgnss',
    version='1.7.7',
    description='Python Package of GNSS data processing',
    # long_description=README,
    author='Liang Zhang',
    author_email='lzhang2019@whu.edu.cn',
    url='https://gitee.com/snnugiser/ppgnss',
    # license=LICENSE,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        "numpy>=1.19.5",
        "matplotlib>=3.3.3",
        "pandas>=0.25.3",
        "xarray>=0.16.2",
        "wget>=3.2",
        "cartopy",
        "h5py>=3.14.0"
    ],
    entry_points={
        'console_scripts': [
            'ppget = ppgnss.ppget:main',
            'pptime = ppgnss.pptime:main',
            'ppsubnet = ppgnss.ppsubnet:main',
        ],
    },
)

