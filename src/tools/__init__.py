"""Tool registry and execution - PROVIDED"""

# Import all tools
from .ci_runner import run_ci_pipeline
from .file_analyzer import analyze_file, analyze_test_failure
from .syntax_fixer import fix_syntax_error
from .import_manager import add_import, remove_unused_import
from .test_fixer import fix_test_assertion
from .dependency_manager import add_dependency
from .config_fixer import validate_config, fix_yaml_syntax

known_actions = {
    "run_ci_pipeline": "Check CI status",
    "analyze_file": "Read file content and identify errors", 
    "analyze_test_failure": "Analyze specific test failure",
    "validate_config": "Check YAML/config syntax",
    "fix_syntax_error": "Fix Python syntax errors",
    "add_import": "Add missing import statement",
    "remove_unused_import": "Remove unused import statement",
    "fix_test_assertion": "Fix wrong test assertion",
    "add_dependency": "Add package to requirements.txt",
    "fix_yaml_syntax": "Fix YAML syntax errors"
}

def execute_action(action_name, params):
    """Execute a tool action"""
    if action_name == "run_ci_pipeline":
        return run_ci_pipeline()
    elif action_name == "analyze_file":
        return analyze_file(params)
    elif action_name == "analyze_test_failure":
        return analyze_test_failure(params)
    elif action_name == "validate_config":
        return validate_config(params)
    elif action_name == "fix_syntax_error":
        return fix_syntax_error(params)
    elif action_name == "add_import":
        return add_import(params)
    elif action_name == "remove_unused_import":
        return remove_unused_import(params)
    elif action_name == "fix_test_assertion":
        return fix_test_assertion(params)
    elif action_name == "add_dependency":
        return add_dependency(params)
    elif action_name == "fix_yaml_syntax":
        return fix_yaml_syntax(params)
    else:
        return {"action": "unknown_action", "status": "fail", "error": f"Unknown action: {action_name}"}

# All tool implementations are now in separate files
