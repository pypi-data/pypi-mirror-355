#!/usr/bin/env python3

import os
import sys

from setuptools import find_packages, setup

if sys.version_info < (3, 10):
    raise ValueError("Requires Python 3.10+")


def requires_from_file(filename: str) -> list:
    with open(filename, "r", encoding="utf-8") as f:
        return [x.strip() for x in f if x.strip()]


with open("DESCRIPTION.md", "r", encoding="utf-8") as f:
    description = f.read()

setup(
    name="snowcross",
    version=os.getenv("VERSION", "0.0.0-dev"),
    description="Adaptors for tools and services in a Snowflake-centric data platform",
    long_description=description,
    long_description_content_type="text/markdown",
    license="Apache License 2.0",
    packages=find_packages(exclude=["tests"]),
    test_suite="tests",
    install_requires=requires_from_file("requirements.txt"),
    extras_require={
        "aws": requires_from_file("requirements-aws.txt"),
        "locator": requires_from_file("requirements-locator.txt"),
    },
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
    ],
)
