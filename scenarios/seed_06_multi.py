"""Seed 06: Multi-Step Chain - Multiple Issues - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce multiple related issues: syntax + test failure (simplified)"""
    
    workspace = Path(workspace_path)
    
    # 1. Simple syntax error in calculator.py
    calc_file = workspace / "calculator.py"
    content = calc_file.read_text()
    
    # Just break syntax - remove colon from divide function
    broken_content = '''"""Simple calculator functions"""

def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def multiply(a, b):
    return a * b


def divide(a, b)  # Missing colon (syntax issue)
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
'''
    
    calc_file.write_text(broken_content)
    
    # 2. Wrong test assertion (only after syntax is fixed)
    test_file = workspace / "tests" / "test_calculator.py"
    test_content = test_file.read_text()
    
    # Break divide test assertion
    broken_test = test_content.replace(
        "assert divide(10, 2) == 5",
        "assert divide(10, 2) == 4"  # Wrong expected value
    )
    
    test_file.write_text(broken_test)
    
    return {
        "seed": "06_multi",
        "description": "Multiple issues: syntax + test failure",
        "error_types": ["SyntaxError", "AssertionError"],
        "files": ["calculator.py", "tests/test_calculator.py"],
        "expected_fixes": ["add_colon", "fix_assertion"]
    }
