from setuptools import setup, find_packages

setup(
    name="algozen",
    version="1.2.0",
    packages=find_packages(),
    install_requires=[],
    author="AlgoZen Team",
    author_email="info@algozen.dev",
    description="Comprehensive Data Structures, Algorithms, and Design Patterns Library",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/algozen/algozen",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Education",
        "Topic :: Scientific/Engineering :: Mathematics",

        "Topic :: Software Development :: Testing",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Development Status :: 5 - Production/Stable"
    ],
    python_requires=">=3.7",
    keywords="algorithms, data structures, design patterns, interview preparation, system design"
)