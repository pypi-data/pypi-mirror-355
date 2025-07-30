from setuptools import setup
import setuptools

import blogsmith

with open("blogsmith/requirements.txt") as f:
    required = f.read().splitlines()
with open("README.md", "r") as f:
    long_description = f.read()

version = blogsmith.__version__
setup(
    name="blogsmith",
    version=version,
    description="Automatic LLM-based multi-agent blog builder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ptarau/blogsmith.git",
    author="Paul Tarau",
    author_email="ptarau@gmail.com",
    license="MIT",
    packages=setuptools.find_packages(),
    package_data={"blogsmith": ["*.txt"]},
    include_package_data=True,
    install_requires=required,
    zip_safe=False,
)
