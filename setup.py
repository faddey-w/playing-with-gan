#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="playing_with_gan",
    version="0.1.0",
    packages=find_packages(include=["playing_with_gan*"]),
    install_requires=[
        "boto3==1.14.48",
        "torch==1.4.0",
        "torchvision==0.5.0",
        "pandas==1.0.5",
        "numpy==1.19.2",
        "sagemaker==2.15.0",
    ],
)
