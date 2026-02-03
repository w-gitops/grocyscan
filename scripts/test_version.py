#!/usr/bin/env python3
"""Test version loading."""
import tomllib
from pathlib import Path

# Test 1: Direct load from pyproject.toml
pyproject = Path(__file__).parent.parent / "pyproject.toml"
print(f"Looking for: {pyproject}")
print(f"Exists: {pyproject.exists()}")

if pyproject.exists():
    with open(pyproject, "rb") as f:
        data = tomllib.load(f)
    print(f"Version from pyproject.toml: {data['project']['version']}")

# Test 2: Import the config module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from app.config import settings
print(f"Version from settings: {settings.grocyscan_version}")
