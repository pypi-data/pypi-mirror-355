from setuptools import setup, find_packages

VERSION = "1.0.3"
DESCRIPTION = "A simple Python library to split large text files into smaller parts."
LONG_DESCRIPTION = "A Python package to split large text files into smaller parts easily."

# Setting up
setup(
    name="file-splitter-harsh",
    version=VERSION,
    author="Harsh Mendapara",
    author_email="mendapara.harsh47@gmail.com",
    description=DESCRIPTION,
    long_description_content_type="text/markdown",
    long_description=open("README.md").read(),
    packages=find_packages(),
    install_requires=[],
    url="https://github.com/harshh351998/filesplitter.git",
    download_url="https://github.com/harshh351998/filesplitter/archive/refs/tags/1.0.0.tar.gz",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
