#!/usr/bin/env python3
"""Test file for import filtering with edge cases."""

# Regular imports
import os
import sys
from pathlib import Path

# Multi-line import with parentheses
from collections import defaultdict, Counter, OrderedDict

# Multi-line import with backslash continuation
from typing import Dict, List, Optional

# More standard library imports
import json
from datetime import datetime

# Local module imports to test our filtering
import test_module
from test_module import utility_function, TestClass

# Mixed import scenarios
from urllib.parse import urlparse

# Triple-quoted string containing what looks like imports
code_example = """
import fake_module
from fake_module import something
"""

another_string = """
This is also a triple-quoted string
import another_fake_module
from yet_another_fake import stuff
"""


def example_function():
    """
    Function with docstring containing imports:
    import docstring_fake
    from docstring_fake import example
    """
    # Use the imported items
    result = utility_function()
    obj = TestClass("test")

    # Use some standard library functions
    data = json.dumps({"result": result, "value": obj.get_value(), "time": str(datetime.now())})

    return data


if __name__ == "__main__":
    print("Test file for import filtering")
    print(example_function())

    # Use some more imports
    path = Path(".")
    url = urlparse("https://example.com")
    print(f"Current directory: {path}")
    print(f"URL scheme: {url.scheme}")
