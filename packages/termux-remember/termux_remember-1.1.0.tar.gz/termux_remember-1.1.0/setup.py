# -*- coding: utf-8 -*-
from setuptools import setup

setup(
    name="termux-remember",
    version="1.1.0",
    author="Mallik Mohammad Musaddiq",
    author_email="mallikmusaddiq1@gmail.com",
    description="Secure CLI note keeper for Termux with tagging and password protection",
    url="https://github.com/mallikmusaddiq1/termux-remember",
    py_modules=[],
    packages=["termux_remember"],
    entry_points={
        "console_scripts": [
            "remember=termux_remember.main:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities"
    ],
    python_requires='>=3.6',
)