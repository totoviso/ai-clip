from setuptools import setup, find_packages
import os
import re

# Read version from src/__init__.py
with open(os.path.join('src', '__init__.py'), 'r', encoding='utf-8') as f:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", f.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string in src/__init__.py")

# Read requirements from requirements.txt
with open('requirements.txt', 'r', encoding='utf-8') as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]

# Read long description from README.md
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="clipmaster",
    version=version,
    author="ClipMaster Team",
    author_email="info@clipmaster.example.com",
    description="Self-hosted video clipping software with YouTube integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/clipmaster/clipmaster",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Video :: Conversion",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "clipmaster=src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.dat", "*.xml"],
    },
)
