from setuptools import setup, find_packages
from pathlib import Path

# Lê o conteúdo do README.md
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="p03py",
    version="1.0.0",
    description="Biblioteca para comunicação com balanças industriais via protocolo P03 (serial ou TCP/IP)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ronei Toporcov",
    author_email="toporcov@hotmail.com",
    url="https://github.com/roneitop/p03py",
    packages=["p03py"],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
