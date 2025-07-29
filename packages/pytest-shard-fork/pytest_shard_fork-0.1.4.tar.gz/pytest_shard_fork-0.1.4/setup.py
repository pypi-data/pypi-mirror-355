#!/usr/bin/env python3
"""
Backward compatibility setup.py that defers to pyproject.toml.

New installations should use pip install, which supports PEP 517/518.
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
