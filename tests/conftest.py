"""Shared pytest configuration — make api/ importable from tests/."""
import os
import sys

# Add api/ to sys.path so `from engines.foo import bar` works.
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
API_DIR = os.path.join(ROOT, "api")
sys.path.insert(0, API_DIR)
