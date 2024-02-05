"""Python driver and command line tool for Honeywell Midas gas detectors."""
from sys import version_info

from setuptools import setup

if version_info < (3, 8):
    raise ImportError("This module requires Python >=3.8.  Use 0.5.1 for Python3.7")

with open('README.md') as in_file:
    long_description = in_file.read()

setup(
    name="midas",
    version="0.6.6",
    description="Python driver for Honeywell Midas gas detectors.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/numat/midas/",
    author="Patrick Fuller",
    author_email="pat@numat-tech.com",
    maintainer="Alex Ruddick",
    maintainer_email="alex@numat-tech.com",
    packages=['midas'],
    package_data={'midas': ['faults.csv', 'py.typed']},
    install_requires=[
        'pymodbus>=2.4.0; python_version == "3.8"',
        'pymodbus>=2.4.0; python_version == "3.9"',
        'pymodbus>=3.0.2,<3.7.0; python_version >= "3.10"',
    ],
    extras_require={
        'test': [
            'mypy>=1.1.1',
            'pytest',
            'pytest-cov',
            'pytest-asyncio',
            'ruff==0.2.0',
        ],
    },
    entry_points={
        'console_scripts': [('midas = midas:command_line')]
    },
    license='GPLv2',
    classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)
