from setuptools import setup, find_packages

setup(
    name="numbyy",
    version="0.4.0",
    author="TM",
    author_email="moldovskiitimur@gmail.com",
    description="Package with sorting algorithms implementation",
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/my_package",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[],
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/my_package/issues",
    },
)