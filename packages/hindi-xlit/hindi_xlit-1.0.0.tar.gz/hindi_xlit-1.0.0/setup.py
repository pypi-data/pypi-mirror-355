"""
Setup script for Hindi Transliteration Library
"""

from setuptools import setup, find_packages
import os
import re

# Read the contents of README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read the contents of requirements.txt
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith('#')]

# Get the version from the package
with open(os.path.join("hindi_xlit", "__init__.py"), "r", encoding="utf-8") as fh:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", fh.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")

setup(
    name="hindi_xlit",
    version=version,
    author="Aman Ranjan Verma",
    author_email="aman.ranjanverma@gmail.com",
    description="A Hindi transliteration package using AI4Bharat's model",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arverma/HindiXlit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Text Processing :: Linguistic",
        "Natural Language :: Hindi",
        "Natural Language :: English",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "hindi-xlit=hindi_xlit.interactive_transliterate:main",
        ],
    },
    include_package_data=True,
    package_data={
        "hindi_xlit": [
            "models/hindi/*.pth",
            "models/hindi/*.json",
        ],
    },
    zip_safe=False,  # Required for package data
) 