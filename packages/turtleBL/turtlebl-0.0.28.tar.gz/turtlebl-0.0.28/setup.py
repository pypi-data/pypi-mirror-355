import os
from setuptools import setup, find_packages

root = os.path.abspath(os.path.dirname(__file__))
version_file = os.path.join(root, "tests", "verstion.txt")

setup(
    name="turtleBL",
    version=open(version_file).read().strip(),
    author="Back",
    description="A Python library for running small bots in the Roblox game Build Logic",
    long_description=open(os.path.join(root, "README.md"), encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    license="GPL-3.0-or-later",
    license_files=["LICENSE"],
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
