import os
from setuptools import setup, find_packages

# Read the contents of your README file
with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="krypton-sdk",  # Name of the package
    version="0.2.1",
    description="A lightweight SDK to connect to a Krypton AI Gateway over the internet.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Saajan",
    author_email="saajan.varghese.2006@gmail.com",
    url="https://github.com/saaj376/Krypton",  
    packages=find_packages(), # Automatically find 'krypton_sdk' folder
    install_requires=[
        "httpx>=0.28.0", # The only dependency needed to make HTTP requests
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
