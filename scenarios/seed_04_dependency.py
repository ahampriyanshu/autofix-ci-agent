"""Seed 04: Missing Dependency - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce dependency error: use numpy without adding to requirements"""
    
    calc_file = Path(workspace_path) / "calculator.py"
    
    # Read original content
    content = calc_file.read_text()
    
    # Add function that uses numpy
    new_function = '''
import numpy as np

def array_sum(arr):
    return np.sum(arr)
'''
    
    # Insert at beginning
    broken_content = new_function + content
    
    # Write broken version
    calc_file.write_text(broken_content)
    
    return {
        "seed": "04_dependency",
        "description": "Missing numpy dependency",
        "error_type": "ModuleNotFoundError", 
        "file": "calculator.py",
        "line": 2,
        "expected_fix": "add_dependency:numpy"
    }
