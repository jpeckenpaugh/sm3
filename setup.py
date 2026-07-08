"""
setup.py — genesis-sm package definition.

Equivalent to pyproject.toml, but written in .py because rules
prevent .toml edits. This is functionally identical.
"""

from setuptools import setup, find_packages

setup(
    name="genesis-sm",
    version="0.0.1.dev4",
    description="DB-driven state machine engine for agentic sprint orchestration",
    author="The Trimurti — Saraswati, Matsya, Kurma",
    license="MIT",
    python_requires=">=3.10",
    install_requires=[],  # pure standard library — opencode CLI is called via subprocess
    package_dir={"": "src"},
    packages=find_packages(where="src", include=["genesis_sm", "genesis_sm.*"]),
    package_data={
        "genesis_sm": ["schema.sql", "config.json"],
    },
    entry_points={
        "console_scripts": [
            "sm=genesis_sm.cli:main",
        ],
    },
    url="https://github.com/jpeckenpaugh/sm3",
)
