"""Seed Lint: PEP8 Linting Errors - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce PEP8 linting errors: missing blank lines"""
    
    calc_file = Path(workspace_path) / "calculator.py"
    
    # Create content with E302 linting errors (missing blank lines before function definitions)
    broken_content = '''"""Simple calculator functions"""
def add(a, b):
    return a + b


def subtract(a, b):
    return a - b
def multiply(a, b):
    return a * b


def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
    
    calc_file.write_text(broken_content)
    
    return {
        "seed": "lint",
        "description": "PEP8 linting errors (E302 missing blank lines)",
        "error_type": "LintingError",
        "file": "calculator.py",
        "line": 2,
        "expected_fix": "add_blank_lines"
    }

