from setuptools import setup, find_packages
import pathlib
from fa2svg._version import __version__

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# Read the README.md for the long description
long_description = (HERE / "README.md").read_text(encoding="utf-8")

setup(
    name="fa2svg",
    version=__version__,  # use version from _version.py
    description="Convert Font Awesome HTML tags into inline SVG",
    long_description=long_description,
    long_description_content_type="text/markdown",

    author="meena-erian",
    url="https://github.com/meena-erian/fa2svg",
    project_urls={
        "Source": "https://github.com/meena-erian/fa2svg",
        "Issue Tracker": "https://github.com/meena-erian/fa2svg/issues",
    },

    packages=find_packages(),
    include_package_data=True,    # ensure README, LICENSE, etc. are included
    install_requires=[
        "beautifulsoup4",
        "lxml",
        "requests",
        "cairosvg",
    ],
    python_requires=">=3.6",
)
