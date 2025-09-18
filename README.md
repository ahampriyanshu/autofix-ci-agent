# Problem Statement: AI-Powered CI AutoFix Agent (ReAct)

Your CI pipeline breaks daily with syntax errors, import issues, test failures, and configuration problems. Instead of manually debugging and fixing each issue, build an AI agent that automatically diagnoses and fixes CI failures.

---

## Task

Build an AI agent using the ReAct (Reason-Act-Observe) pattern that:
- Uses **Reasoning** to analyze CI failures and plan fixes systematically.
- Uses **Actions** to execute targeted fixes using specialized tools.
- Uses **Observations** to interpret results and determine next steps.
- Orchestrates multiple fix attempts until CI passes or max iterations reached.
- Returns a structured JSON output with fix results.

---

## Requirements

- Implement a ReAct-based agent with three core methods:

  ### 1) Reason
          - **Uses LLM** to analyze current CI state and plan next action.
          - **Produces structured reasoning** with specific tool calls and parameters.

  ### 2) Act
      - **Executes tool calls** from the reasoning step with proper error handling.
      - **Uses specialized tools** for different types of fixes (syntax, imports, tests, config).
      - **Handles tool failures** gracefully and reports errors for observation.
      
      **Available Tools:**
        - **run_ci_pipeline** - Check current CI status and identify failures
        - **analyze_file** - Read and analyze file content for errors
          - Input: filename (e.g., "calculator.py")
          - Output: File content with error analysis
        - **analyze_test_failure** - Analyze specific test failure details
          - Input: test_path (e.g., "tests/test_calculator.py")
          - Output: Test failure analysis and suggested fixes
        - **fix_syntax_error** - Fix Python syntax errors
          - Input: "file:line:fix_type" (e.g., "calculator.py:3:add_colon")
          - Output: Fix result with updated file content
        - **add_import** - Add missing import statements
          - Input: "file:import_statement" (e.g., "calculator.py:import math")
          - Output: Updated file with new import
        - **remove_unused_import** - Remove unused import statements
          - Input: "file:import_statement" (e.g., "calculator.py:import os")
          - Output: Updated file with import removed
        - **fix_test_assertion** - Fix incorrect test assertions
          - Input: "file:line:correct_value" (e.g., "tests/test_calc.py:21:5.0")
          - Output: Updated test with correct assertion
        - **add_dependency** - Add missing packages to requirements.txt
          - Input: package_name (e.g., "numpy==1.21.0")
          - Output: Updated requirements.txt
        - **validate_config** - Check YAML/config file syntax
          - Input: filename (e.g., "ci/ci_config.yml")
          - Output: Validation results and error details
        - **fix_yaml_syntax** - Fix YAML syntax errors
          - Input: "file:line:fix_type" (e.g., "ci_config.yml:5:fix_indentation")
          - Output: Fixed YAML file

  ### 3) Observe
        - **Interprets action results** and determines CI status (pass/fail/unknown).
        - **Tracks progress** toward successful CI completion.
        - **Decides continuation** - whether more actions are needed or task is complete.
        - **Handles errors** by providing clear feedback for next reasoning step.

---

## Error Scenarios

The agent handles various CI failure types:

### 1) Syntax Errors
- Missing colons in function definitions
- Incorrect indentation
- Unclosed brackets or quotes
- Invalid Python syntax

### 2) Import Issues
- Missing import statements
- Unused imports causing linting failures
- Incorrect module names

### 3) Test Failures
- Wrong assertion values
- Missing test dependencies
- Incorrect test logic

### 4) Configuration Problems
- YAML syntax errors
- Missing configuration values
- Invalid file paths

### 5) Dependency Issues
- Missing packages in requirements.txt
- Version conflicts
- Import errors from missing dependencies

---

## Examples

### Success Example - Syntax Error Fix

**Initial CI Failure:**
```
SyntaxError: invalid syntax (calculator.py, line 3)
```

#### Reasoning Step
```json
{
  "reasoning": "CI pipeline failed with syntax error in calculator.py line 3. Need to analyze the file to identify the specific syntax issue.",
  "tool_call": {
    "tool": "analyze_file",
    "input": "calculator.py"
  }
}
```

#### Action Result
```json
{
  "status": "success",
  "action": "analyze_file",
  "result": {
    "status": "pass",
    "data": {
      "content": "def add(a, b)\n    return a + b",
      "errors": ["Missing colon after function definition on line 3"]
    }
  }
}
```

#### Observation
```json
{
  "observation": "Found missing colon in function definition on line 3. This is a syntax error that needs immediate fixing.",
  "ci_status": "fail",
  "next_action_needed": true
}
```

#### Next Reasoning Step
```json
{
  "reasoning": "Identified missing colon in function definition. Need to fix this syntax error using fix_syntax_error tool.",
  "tool_call": {
    "tool": "fix_syntax_error",
    "input": "calculator.py:3:add_colon"
  }
}
```

#### Final Action Result
```json
{
  "status": "success",
  "action": "fix_syntax_error",
  "result": {
    "status": "pass",
    "data": {
      "fixed": true,
      "content": "def add(a, b):\n    return a + b"
    }
  }
}
```

### Error Example - Tool Failure

**CI Failure with Tool Error:**

#### Reasoning Step
```json
{
  "reasoning": "Need to fix YAML syntax error in configuration file.",
  "tool_call": {
    "tool": "fix_yaml_syntax",
    "input": "ci_config.yml:5:fix_indentation"
  }
}
```

#### Action Result (Failure)
```json
{
  "status": "error",
  "error": "File ci_config.yml not found in workspace"
}
```

#### Observation
```json
{
  "observation": "Error occurred: File ci_config.yml not found in workspace. Need to check file location or use correct path.",
  "ci_status": "unknown",
  "next_action_needed": true
}
```

---

## Constraints

- All reasoning outputs must be valid JSON with "reasoning" and "tool_call" fields.
- Maximum 10 iterations to prevent infinite loops.
- Must use provided tools and helpers:
  - src/llm.py → for LLM calls
  - src/tools/ → for all fix tools
  - src/prompts/ci_agent_prompt.txt → for agent instructions
