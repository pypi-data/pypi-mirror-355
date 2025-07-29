from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="ophelos-sdk",
    version="1.0.2",
    author="Ophelos",
    author_email="support@ophelos.com",
    description="Python SDK for the Ophelos API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tomasz-oph/ophelos_python_sdk",
    packages=find_packages(),
    classifiers=[
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    keywords="ophelos api sdk debt management payments",
    project_urls={
        "Bug Reports": "https://github.com/tomasz-oph/ophelos_python_sdk/issues",
        "Source": "https://github.com/tomasz-oph/ophelos_python_sdk",
    },
)
