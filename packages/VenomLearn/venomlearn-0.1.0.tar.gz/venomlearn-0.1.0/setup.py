from setuptools import setup, find_packages

setup(
    name="VenomLearn",
    version="0.1.0",
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