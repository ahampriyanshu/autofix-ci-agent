"""Seed 03: Test Failure - Wrong Assertion - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce test failure: wrong assertion value"""
    
    test_file = Path(workspace_path) / "tests" / "test_calculator.py"
    
    # Read original content
    content = test_file.read_text()
    
    # Break test assertion
    broken_content = content.replace(
        "assert add(2, 3) == 5",
        "assert add(2, 3) == 6"  # Wrong expected value
    )
    
    # Write broken version
    test_file.write_text(broken_content)
    
    return {
        "seed": "03_test",
        "description": "Wrong test assertion value", 
        "error_type": "AssertionError",
        "file": "tests/test_calculator.py",
        "line": 6,
        "expected_fix": "fix_assertion:5"
    }
