from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="rithmetic",
    version="0.0.10",
    description="Python package to convert Numbers from one base to another",
    package_dir={"": "rithmetic"},
    packages=find_packages(where="rithmetic"),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Prashant-Aswal/Numbers_and_Bases",
    author="Prashant Aswal",
    author_email="prashant.aswal89@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    install_requires=[],
    extras_require={
        "dev": ["twine>=4.0.2"],
    },
    python_requires=">=3.10",
)