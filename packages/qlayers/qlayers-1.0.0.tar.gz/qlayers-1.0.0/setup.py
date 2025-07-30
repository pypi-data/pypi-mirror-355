from setuptools import setup, find_packages

# Get requirements from text file
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

# Use README.md as the long description
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="qlayers",
    version="1.0.0",
    description="Quantitative layer analysis for renal MRI",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexdaniel654/qlayers",
    license="GPL-3.0",
    python_requires=">=3.9, <4",
    packages=find_packages(),
    install_requires=requirements,
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
