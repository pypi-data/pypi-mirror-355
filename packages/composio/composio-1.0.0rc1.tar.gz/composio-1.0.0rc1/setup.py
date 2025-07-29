"""
Setup configuration for compsio core.
"""

import typing as t
from pathlib import Path

from setuptools import find_packages, setup

COMPOSIO = Path(__file__).parent.resolve() / "composio"


def scan_for_package_data(
    directory: Path,
    package: Path,
    data: t.Optional[t.List[str]] = None,
) -> t.List[str]:
    """Walk the package and scan for package files."""
    data = data or []
    for child in directory.iterdir():
        if child.name.endswith(".py") or child.name.endswith(".pyc"):
            continue

        if child.is_file():
            data.append(str(child.relative_to(package)))
            continue

        data += scan_for_package_data(
            directory=child,
            package=package,
        )
    return data


setup(
    name="composio",
    version="1.0.0rc1",
    author="Composio",
    author_email="tech@composio.dev",
    description="Core package to act as a bridge between composio platform and other services.",
    long_description=(Path(__file__).parent / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    url="https://github.com/composiohq/composio",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9,<4",
    packages=find_packages(include=["composio*"]),
    install_requires=[
        "pysher==1.0.8",
        "pydantic>=2.6.4",
        "composio-client",
        "typing-extensions>=4.0.0",
    ],
    include_package_data=True,
    package_data={
        "composio": scan_for_package_data(
            directory=COMPOSIO,
            package=COMPOSIO,
        ),
    },
)
