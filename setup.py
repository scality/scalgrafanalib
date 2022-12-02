import os
from setuptools import setup, find_packages


def local_file(name: str) -> str:
    return os.path.relpath(os.path.join(os.path.dirname(__file__), name))


README = local_file("README.md")
with open(README, encoding="utf-8") as f:
    DESCRIPTION = f.read()

setup(
    name="scalgrafanalib",
    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="1.1.0",
    description="Library for building Grafana dashboards at scality",
    long_description=DESCRIPTION,
    url="https://github.com/scality/scalgrafanalib",
    project_urls={
        "Source": "https://github.com/scality/scalgrafanalib",
    },
    author="Scality",
    author_email="support@scality.com",
    license="Apache",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: System :: Monitoring",
    ],
    install_requires=[
        "attrs>=15.2.0",
        "grafanalib==0.6.3",
    ],
    extras_require={
        "dev": [
            "black==22.3.0",
            "mypy==0.931",
            "pylint==2.12.2",
            "pytest==7.1.3",
            "types-setuptools",
        ],
    },
)
