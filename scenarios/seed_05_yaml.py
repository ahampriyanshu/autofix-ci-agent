"""Seed 05: YAML Config Error - Missing Colon - PROVIDED"""

from pathlib import Path

def induce_errors(workspace_path):
    """Induce YAML syntax error: missing colon in config file"""
    
    workspace = Path(workspace_path)
    
    # Create ci_config.yml with syntax error
    config_dir = workspace / "ci"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "ci_config.yml"
    config_file.write_text('''steps:
  - name: test
    run: pytest
  - name lint  # Missing colon
    run: flake8
''')
    
    return {
        "seed": "05_yaml",
        "description": "Missing colon in YAML config",
        "error_type": "YAMLError", 
        "file": "ci/ci_config.yml",
        "line": 4,
        "expected_fix": "add_colon"
    }
