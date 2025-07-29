"""
Setup configuration for flotorch-eval package.
"""

from setuptools import find_packages, setup

setup(
    name="flotorch-eval",
    version="0.2.4",
    description="A comprehensive evaluation framework for AI systems",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Nanda Rajashekaruni",
    author_email="nanda@flotorch.ai",
    url="https://github.com/flotorch/flotorch-eval",
    packages=find_packages(),
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
