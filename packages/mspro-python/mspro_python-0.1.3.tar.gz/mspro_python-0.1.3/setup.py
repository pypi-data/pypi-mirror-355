# setup.py

from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="mspro-python",
    version="0.1.3",
    description="FastAPI项目脚手架",
    author="JENA",
    author_email="jena.want@gmail.com",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click"
    ],
    entry_points={
        "console_scripts": [
            "mspro-init = mspro_python.cli:main"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Framework :: FastAPI",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],
    python_requires=">=3.10",
    long_description=long_description,
    long_description_content_type="text/markdown",
)

# rm -rf dist/ build/ *.egg-info && python setup.py sdist bdist_wheel && twine upload dist/*
