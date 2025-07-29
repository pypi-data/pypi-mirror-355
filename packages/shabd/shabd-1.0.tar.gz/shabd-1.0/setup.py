from setuptools import setup, find_packages
import os


def load_requirements(filename):
    """Load requirements from a file."""
    requirements = []
    if os.path.isfile(filename):
        with open(filename, "r") as file:
            requirements = file.read().splitlines()
    return requirements


setup(
    name="shabd",
    version="1.0",
    packages=find_packages(),
    install_requires=load_requirements("requirements.txt"),
    entry_points={
        "console_scripts": [
            "shabd=shabd.shabd:main",
        ],
    },
    description="A command-line English dictionary tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/spignelon/shabd",
    author="Ujjawal Saini",
    author_email="spignelon@proton.me",
    license="GPL-3.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Education",
        "Topic :: Utilities",
    ],
    python_requires=">=3.9",
)
