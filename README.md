All PRs in your team need to pass CI checks before merging. Developers often spend time fixing basic lint and syntax issues to get their PRs approved. This manual debugging is time-consuming and blocks productivity. You are given the task to automate this process by building an intelligent agent that automatically detects, diagnoses, and resolves these issues.

### Task

Build an AI agent using the ReAct (Reason-Act-Observe) pattern that:

- Uses **Reasoning** to analyze CI failures and plan fixes
- Uses **Actions** to execute targeted fixes using tools
- Orchestrates multiple fix attempts until CI passes
- Returns structured JSON output

### Requirements

To complete this task, you need to implement:

#### 1. Core Agent Methods

Implement two methods in `src/agent.py`:

- **reason()** - Analyzes current CI state and plans next action using LLM
- **act()** - Executes tool calls with proper error handling

Note: The **observe()** method is already implemented.

#### 2. Available Tools

The agent has access to these tools:

- **run_ci_pipeline** - Check CI status and identify failures
- **analyze_file** - Read and analyze file content
- **fix_syntax_error** - Fix Python syntax errors
- **add_import** - Add missing import statements

#### 3. Error Scenarios

Your agent must handle:

**Syntax Errors:** Missing colons, incorrect indentation, invalid Python syntax

**Import Issues:** Missing import statements, NameError from undefined modules

**Linting Errors:** PEP8 violations

### Sample Cases

#### Case 1: Syntax Error Fix

**Initial State:**
```
SyntaxError: invalid syntax (calculator.py, line 3)
```

**Reasoning:**
```json
{
  "reasoning": "CI pipeline failed with syntax error in calculator.py line 3. Need to analyze the file to identify the specific syntax issue.",
  "tool_call": {
    "tool": "analyze_file",
    "input": "calculator.py"
  }
}
```

**Action Result:**
```json
{
  "status": "success",
  "action": "analyze_file",
  "result": {
    "status": "pass",
    "data": {
      "content": "def add(a, b)\n    return a + b"
    }
  }
}
```

**Observation:**
```json
{
  "observation": "Found missing colon in function definition on line 3.",
  "ci_status": "fail",
  "next_action_needed": true
}
```

**Next Reasoning:**
```json
{
  "reasoning": "Identified missing colon in function definition. Fixing it now.",
  "tool_call": {
    "tool": "fix_syntax_error",
    "input": "calculator.py:3:add_colon"
  }
}
```

**Verification:**
```json
{
  "reasoning": "Syntax error fixed. Running CI to verify.",
  "tool_call": {
    "tool": "run_ci_pipeline",
    "input": ""
  }
}
```

**Final Result:**
```json
{
  "observation": "CI pipeline now passes successfully.",
  "ci_status": "pass",
  "next_action_needed": false
}
```

#### Case 2: Missing Import

**Initial State:**
```
NameError: name 'math' is not defined (calculator.py, line 15)
```

**Reasoning:**
```json
{
  "reasoning": "CI failing with NameError for math module. Adding import statement.",
  "tool_call": {
    "tool": "add_import",
    "input": "calculator.py:import math"
  }
}
```

**Verification:**
```json
{
  "reasoning": "Import added. Verifying by running CI.",
  "tool_call": {
    "tool": "run_ci_pipeline",
    "input": ""
  }
}
```

### Best Practices

**Systematic Workflow:** Follow the 5-step approach:
1. Run CI pipeline to identify failures
2. Analyze files to understand errors
3. Apply appropriate fixes
4. Verify fixes by running CI again
5. Repeat until CI passes

**Error Detection:** Use error patterns to choose the right tool:
- `SyntaxError` → use `fix_syntax_error`
- `NameError` → use `add_import`
- `E302 linting error` → use `fix_syntax_error` with `add_blank_lines`

**JSON Output:** Always output valid JSON with "reasoning" and "tool_call" fields

**Exact Paths:** Use exact file paths from error messages (don't modify them)

**Iteration Limit:** Maximum 10 iterations to prevent infinite loops

**Interactive Testing:** Use the Streamlit UI (`streamlit run app.py`) to test your agent
