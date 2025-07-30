import os
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="logviz",
    version=0.3,  
    author="Owusu Kenneth",
    author_email="okwesi73@gmail.com",
    description="LogViz: A Python logging library for visualized, structured, and customizable console output.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/okwesi/LogViz",
    packages=find_packages(),
    install_requires=[],  # Add any dependencies your package requires
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Logging",
    ],
    python_requires='>=3.8',
    license_files="LICENSE",
)
