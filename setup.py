from setuptools import setup

setup(
    name="midas",
    version="0.1.1",
    description="Python driver for Honeywell Midas gas dectectors.",
    url="http://github.com/numat/midas/",
    author="Patrick Fuller",
    author_email="pat@numat-tech.com",
    packages=["midas"],
    install_requires=["pymodbus"],
    entry_points={
        "console_scripts": [("midas = midas:command_line")]
    },
    license="GPLv2",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)"
    ]
)
