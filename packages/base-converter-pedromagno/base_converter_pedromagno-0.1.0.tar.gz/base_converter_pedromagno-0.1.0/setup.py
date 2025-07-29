from tkinter.font import names

from setuptools import setup, find_packages

setup(
    name="base_converter_pedromagno",
    version="0.1.0",
    description="Base conversion library (base 2 to 16) with decimal and fractional support.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Pedro Magno",
    author_email="pedromagnopro@gmail.com",
    url="https://github.com/PedroMagno11/base_converter",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)