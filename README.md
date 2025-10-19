When CI pipelines fail due to syntax errors or missing dependencies, manual debugging takes valuable developer time. Build an intelligent agent that automatically detects, diagnoses, and resolves these issues to keep your pipeline running smoothly.

### Task

Build an AI agent using the ReAct (Reason-Act-Observe) pattern that:

- Uses **Reasoning** to analyze CI failures and plan fixes systematically.
- Uses **Actions** to execute targeted fixes using specialized tools.
- Uses **Observations** to interpret results and determine next steps.
- Orchestrates multiple fix attempts until CI passes or max iterations reached.
- Returns a structured JSON output.

### Requirements

To complete the system, you need to implement the following:

#### 1. Core Agent Methods

Implement two core methods in `src/ci_agent.py`:

- **reason()** - Analyzes current CI state and plans next action using LLM
- **act()** - Executes tool calls with proper error handling

Note: The **observe()** method is already implemented for you.

#### 2. Prompt File

The prompt file that defines agent behavior is already provided with a systematic approach:

- `src/prompts/ci_agent_prompt.txt`: Pre-written prompt with clear workflow and examples
  - Defines a 5-step systematic approach
  - Provides explicit error type detection rules
  - Includes deterministic examples for each tool

#### 3. Available Tools

The agent has access to these tools in `src/tools/`:

- **run_ci_pipeline** - Check CI status and identify failures
- **analyze_file** - Read and analyze file content
- **fix_syntax_error** - Fix Python syntax errors
- **add_import** - Add missing import statements

### Error Scenarios

The agent must handle various CI failure types:

#### 1. Syntax Errors

- Missing colons in function definitions
- Incorrect indentation
- Unclosed brackets or quotes
- Invalid Python syntax

#### 2. Import Issues

- Missing import statements
- NameError from undefined modules or functions

### Sample Cases

#### Case 1: Syntax Error Fix

**Initial CI Failure:**

```
SyntaxError: invalid syntax (calculator.py, line 3)
```

**Reasoning Step**

```json
{
  "reasoning": "CI pipeline failed with syntax error in calculator.py line 3. Need to analyze the file to identify the specific syntax issue.",
  "tool_call": {
    "tool": "analyze_file",
    "input": "calculator.py"
  }
}
```

**Action Result**

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

**Observation**

```json
{
  "observation": "Found missing colon in function definition on line 3. This is a syntax error that needs immediate fixing.",
  "ci_status": "fail",
  "next_action_needed": true
}
```

**Next Reasoning Step**

```json
{
  "reasoning": "Identified missing colon in function definition. Need to fix this syntax error using fix_syntax_error tool.",
  "tool_call": {
    "tool": "fix_syntax_error",
    "input": "calculator.py:3:add_colon"
  }
}
```

**Final Action Result**

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

**Final Observation**

```json
{
  "observation": "Successfully fixed syntax error by adding missing colon. File now has correct Python syntax. Need to run CI pipeline to verify the fix.",
  "ci_status": "unknown",
  "next_action_needed": true
}
```

**Verification Step**

```json
{
  "reasoning": "Syntax error has been fixed. Now need to run CI pipeline to check if there are any remaining issues.",
  "tool_call": {
    "tool": "run_ci_pipeline",
    "input": ""
  }
}
```

**Final CI Result**

```json
{
  "status": "success",
  "action": "run_ci_pipeline",
  "result": {
    "status": "pass",
    "data": {
      "overall_status": "pass",
      "message": "All tests passed successfully"
    }
  }
}
```

**Completion Observation**

```json
{
  "observation": "CI pipeline now passes successfully. All syntax errors have been resolved and tests are passing.",
  "ci_status": "pass",
  "next_action_needed": false
}
```

#### Case 2: Missing Import

**Initial CI Failure:**

```
NameError: name 'math' is not defined (calculator.py, line 15)
```

**Reasoning Step**

```json
{
  "reasoning": "CI failing with NameError for math module. Need to add import statement.",
  "tool_call": {
    "tool": "add_import",
    "input": "calculator.py:import math"
  }
}
```

**Action Result**

```json
{
  "status": "success",
  "action": "add_import",
  "result": {
    "status": "pass",
    "data": {
      "added": "import math",
      "file": "calculator.py"
    }
  }
}
```

**Observation**

```json
{
  "observation": "Successfully added import math to calculator.py. Need to run CI pipeline to verify the fix.",
  "ci_status": "unknown",
  "next_action_needed": true
}
```

**Verification Step**

```json
{
  "reasoning": "Import added. Now need to run CI pipeline to check if the issue is resolved.",
  "tool_call": {
    "tool": "run_ci_pipeline",
    "input": ""
  }
}
```

### Best Practices

- **Systematic Workflow**: Follow the 5-step approach defined in the prompt
  1. Run CI pipeline to identify failures
  2. Analyze files to understand errors
  3. Apply appropriate fixes
  4. Verify fixes by running CI again
  5. Repeat until CI passes
- **Error Detection**: Use the error type patterns to choose the right tool
  - `SyntaxError` → use `fix_syntax_error`
  - `NameError` → use `add_import`
- **JSON Output**: Always output valid JSON with "reasoning" and "tool_call" fields
- **Exact Paths**: Use exact file paths from error messages (don't modify them)
- **Iteration Limit**: Maximum 10 iterations to prevent infinite loops
- **Interactive Testing**: Use the Streamlit UI (`streamlit run app.py`) to test your agent
