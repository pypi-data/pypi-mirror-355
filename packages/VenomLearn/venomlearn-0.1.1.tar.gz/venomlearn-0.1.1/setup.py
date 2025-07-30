from setuptools import setup, find_packages
import pathlib

# Read the contents of README.md for long_description
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="VenomLearn",
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "rich",
        "questionary",
        "pyfiglet",
        "tqdm",
    ],
    author="VenomLearn Team",
    author_email="example@example.com",
    description="An interactive Python learning package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="python, learning, interactive, education",
    url="https://github.com/VenomLearn/VenomLearn",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    entry_points={
        "console_scripts": [
            "venomlearn=VenomLearn.main:main",
        ],
    },
)