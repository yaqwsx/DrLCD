# -*- coding: utf-8 -*-

import setuptools


with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="DrLCD",
    python_requires='>=3.7',
    version="0.1.0",
    author="Jan Mrázek",
    author_email="email@honzamrazek.cz",
    description="TBA",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="TBA",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "click>=7.1",
        "pyserial~=3.5",
        "opencv-python~=4.6",
        "scipy~=1.9",
        "pygame~=2.1",
        "plotly~=5.11"
    ],
    extras_require={
        "dev": ["pytest"],
    },
    entry_points = {
        "console_scripts": [
            "drlcd=drlcd.ui:cli",
        ],
    }
)
