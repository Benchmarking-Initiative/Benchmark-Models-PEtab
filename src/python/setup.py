"""Benchmark-Models-PEtab python package."""

import setuptools
from os import path

here = path.abspath(path.dirname(__file__))


def read(fname):
    with open(fname) as f:
        return f.read()

name = "benchmark_models_petab"

setuptools.setup(
    # Metadata
    name=name,
    version="0.0.0a2",
    description="A collection of models with experimental data in the PEtab format",
    long_description=read(path.join(here, "README.md")),
    long_description_content_type="text/markdown",
    url="https://github.com/Benchmarking-Initiative/Benchmark-Models-PEtab",
    packages=[name],
    # Author
    author="The Benchmark-Models-PEtab maintainers",
    author_email="yannik.schaelte@gmail.com",
    # License
    license="BSD-3-Clause",
    # Requirements
    install_requires=[],
    python_requires=">= 3.8",
    # Data
    include_package_data=True,
)
