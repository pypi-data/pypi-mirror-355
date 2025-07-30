from setuptools import setup, find_packages

setup(
    name="synapseconvert",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "openpyxl",  # required by pandas to read .xlsx files
    ],
    entry_points={
        "console_scripts": [
            "synapse-upconvert = synapseconvert.upconvert:main",
            "synapse-downconvert = synapseconvert.downconvert:main",
        ],
    },
)
