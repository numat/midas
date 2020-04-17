"""Python driver and command line tool for Honeywell Midas gas detectors."""
from setuptools import setup

with open('README.md', 'r') as in_file:
    long_description = in_file.read()

setup(
    name="midas",
    version="0.4.1",
    description="Python driver for Honeywell Midas gas detectors.",
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="http://github.com/numat/midas/",
    author="Patrick Fuller",
    author_email="pat@numat-tech.com",
    packages=['midas'],
    package_data={'midas': ['faults.csv']},
    install_requires=[
        'pymodbus==2.2.0rc1'
    ],
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
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)
