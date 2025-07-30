 

import setuptools
from setuptools import setup, find_packages

long_description = ""
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="code_monger",
    version="0.1.9",
    author="Victor Kipkemboi",
    author_email="scriptilapia@gmail.com",
    long_description =long_description,
    long_description_content_type="text/markdown",
    description="A package for on-the-fly code generation and validation",
    url="https://github.com/victhepythonista/code_monger",
    project_urls={
        "Bug Tracker": "https://github.com/victhepythonista/code_monger/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License"
    ],
    packages=["code_monger"],
    python_requires=">=3.6",
 
)