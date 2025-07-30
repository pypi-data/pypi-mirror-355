from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='badcode_utilities',
    version='0.6',  # or higher, must be unique and not used before
    description='A collection of utility functions for string handling and filtering.',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'badcode_utilities': ['badwords.txt'],
    },
    install_requires=[
        # none
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
)