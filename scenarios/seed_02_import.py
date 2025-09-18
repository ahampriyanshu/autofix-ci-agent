"""Seed 02: Import Error - Missing Import - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce import error: use math module without importing"""
    
    calc_file = Path(workspace_path) / "calculator.py"
    
    # Read original content
    content = calc_file.read_text()
    
    # Add function that uses math without importing
    new_function = '''
def sqrt_calc(x):
    return math.sqrt(x)  # math not imported
'''
    
    # Insert new function after existing functions
    broken_content = content + new_function
    
    # Write broken version
    calc_file.write_text(broken_content)
    
    return {
        "seed": "02_import", 
        "description": "Missing math import",
        "error_type": "NameError",
        "file": "calculator.py",
        "line": 22,
        "expected_fix": "add_import:math"
    }
