from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(    name="faceparser",
    version="1.0.1",
    author="Jayesh J. Pandey",
    author_email="pandeyjayesh020@gmail.com",
    description="A Python library for face parsing and feature extraction",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jayeshpandey01/faceparser",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.7",
    install_requires=[
        "torch>=1.7.0",
        "torchvision>=0.8.0",
        "numpy>=1.19.0",
        "pillow>=8.0.0",
        "click>=7.0",
        "tqdm>=4.0.0",
        "requests>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "faceparser=faceparser.cli:cli",
        ],
    },
)
