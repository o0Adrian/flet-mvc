from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

VERSION = '0.0.1'
DESCRIPTION = 'This package will allow the developer to use an mvc structure in a Flet project.'

# Setting up
setup(
    name="flet-mvc",
    version=VERSION,
    author="o0Adrian (C. Adrián Monroy)",
    author_email="<carlos.monclef@gmail.com>",
    description=DESCRIPTION,
    url='https://github.com/o0Adrian/flet-mvc',
    long_description_content_type="text/markdown",
    long_description=long_description,
    packages=find_packages(),
    install_requires=['flet'],
    keywords=['mvc', 'flet', 'flet mvc', 'model', 'view', 'controller', 'node', 'datapoint'],
    classifiers=[
        "Development Status :: 1 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Operating System :: Unix",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)