from setuptools import setup, find_packages

setup(
    name="superlake",
    version="1.0.3",
    packages=find_packages(),
    install_requires=[
        "pyspark>=3.5.0",
        "delta-spark>=3.1.0",
        "pandas>=1.0.0",
        "pytz",
        "applicationinsights",
        "loguru",
        "mypy",
        "pytest",
    ],
    author="Loïc Magnien",
    author_email="loic.magnien@gmail.com",
    description="A modern, intuitive Python package for data lakehouse operations",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/loicmagnien/superlake",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.7",
)