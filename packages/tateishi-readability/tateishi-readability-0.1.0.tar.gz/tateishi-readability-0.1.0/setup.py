from setuptools import setup
from setuptools import find_packages
from setuptools.command.install import install

with open('README.md', 'r') as f:
    readme = f.read()

setup(
    name="tateishi-readability",
    version="0.1.0",
    py_modules=["tateishi_readability"],
    install_requires=["divide-char-type"],
    setup_requires=["divide-char-type"],

    # metadata to display on PyPI
    author="Shinya Akagi",
    description="Calculate Readability for Japanese Document using Tateishi Index",
    long_description=readme,
    long_description_content_type='text/markdown',
    url="https://github.com/ShinyaAkagiI/tateishi_readability", 
    license="PSF",
)
