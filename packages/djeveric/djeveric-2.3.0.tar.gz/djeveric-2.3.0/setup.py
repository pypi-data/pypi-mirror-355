import os

from setuptools import find_namespace_packages, setup

__dir__ = os.path.abspath(os.path.dirname(__file__))
__version__ = "2.3.0"

try:
    with open(os.path.join(__dir__, "README.md")) as f:
        long_description = "\n" + f.read()
except FileNotFoundError:
    long_description = ""

setup(
    name="djeveric",
    version=__version__,
    description="Simple email confirmation for django model instances.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://git.hack-hro.de/memoorje/djeveric",
    author="memoorje developers",
    author_email="tach@memoorje.org",
    license="MIT",
    packages=find_namespace_packages(include=["djeveric"]),
    install_requires=[
        "django>=2.2,<6",
        "djangorestframework~=3.10",
    ],
    include_package_data=True,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
