"""Seed 01: Syntax Error - Missing Colon - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce syntax error: missing colon in function definition"""
    
    calc_file = Path(workspace_path) / "calculator.py"
    
    # Read original content
    content = calc_file.read_text()
    
    # Introduce syntax error: remove colon from add function
    broken_content = content.replace(
        "def add(a, b):",
        "def add(a, b)"  # Missing colon
    )
    
    # Write broken version
    calc_file.write_text(broken_content)
    
    return {
        "seed": "syntax",
        "description": "Missing colon in function definition",
        "error_type": "SyntaxError",
        "file": "calculator.py",
        "line": 3,
        "expected_fix": "add_colon"
    }
