from setuptools import setup

setup(
    name="midas",
    version="0.2.13",
    description="Python driver for Honeywell Midas gas dectectors.",
    url="http://github.com/numat/midas/",
    author="Patrick Fuller",
    author_email="pat@numat-tech.com",
    packages=['midas'],
    package_data={'midas': ['midas/faults.csv']},
    include_package_data=True,
    install_requires=[
        'pymodbus3;python_version>"3.0"',
        'pymodbus;python_version<"3.0"'
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: Human Machine Interfaces'
    ]
)
