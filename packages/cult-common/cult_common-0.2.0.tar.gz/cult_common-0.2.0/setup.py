# setup.py
from setuptools import setup, find_packages

setup(
    name="cult-common", # Make sure this name is unique on PyPI if it's your first time for this package name
    version="0.2.0", # Increment this version
    description="Shared utilities, schemas, and mixins for Cult microservices",
    author="Oluwaseun Ayeni",
    license="MIT",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    author_email="Oluwastormy@gmail.com",
    url="https://github.com/Oluwaseun-ayeni/cult-common",
    packages=find_packages(include=["cult_common", "cult_common.*"]),
    install_requires=[
        "pydantic>=1.10",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
        ],
    },
    python_requires=">=3.8",
)
