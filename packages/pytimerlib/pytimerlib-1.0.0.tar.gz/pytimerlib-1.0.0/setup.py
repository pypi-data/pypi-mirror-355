from setuptools import setup, find_packages

setup(
    name="pytimerlib",
    version="1.0.0",
    author="clxakz",
    description="A simple timer library for PyGame",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/clxakz/pytimer",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "pytweening"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
