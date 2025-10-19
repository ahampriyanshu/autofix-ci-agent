"""Seed 06: Multi-Step - Multiple Syntax Errors - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce multiple syntax errors in the same file"""
    
    workspace = Path(workspace_path)
    
    # Add multiple syntax errors in calculator.py
    calc_file = workspace / "calculator.py"
    
    # Create content with multiple syntax errors
    broken_content = '''"""Simple calculator functions"""

def add(a, b)  # Missing colon (syntax issue 1)
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b)  # Missing colon (syntax issue 2)
    return a * b


def divide(a, b):
    if b == 0
        raise ValueError("Cannot divide by zero")  # Missing colon (syntax issue 3)
    return a / b
'''
    
    calc_file.write_text(broken_content)
    
    return {
        "seed": "multi",
        "description": "Multiple syntax errors in same file",
        "error_types": ["SyntaxError"],
        "files": ["calculator.py"],
        "expected_fixes": ["add_colon", "add_colon", "add_colon"]
    }
