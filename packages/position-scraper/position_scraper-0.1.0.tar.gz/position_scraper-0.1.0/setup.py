from setuptools import setup, find_packages

setup(
    name="position_scraper",  # Name of your library
    version="0.1.0",          # Initial version
    description="A library to scrape and extract robot positions from header files",
    author="Arun CS",
    author_email="aruncs31s@proton.me",
    url="https://github.com/AI-Robot-GCEK/position_scraper", 
    packages=find_packages(), 
    install_requires=[
        "requests",  
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
