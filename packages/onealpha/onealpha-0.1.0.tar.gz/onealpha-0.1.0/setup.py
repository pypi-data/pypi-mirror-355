from setuptools import setup, find_packages

setup(
    name="onealpha",                     # Package name
    version="0.1.0",                     # Version
    author="Alok Vishwakarma",                  # Your name
    author_email="alokvishwakarma@theonealpha.com",  # Your email
    description="TheOneAlpha data downloader",  # Short description
    long_description=open("README.md").read(), # Long description
    long_description_content_type="text/markdown",  # README format
    packages=find_packages(),           # Auto-detect packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
    install_requires=[],  
)
