"""Helper functions for CI Agent"""

import os


def execute_tool_in_workspace(workspace_path, tool_name, params=""):
    """
    Execute a tool in the specified workspace directory.

    Args:
        workspace_path: Path to the workspace directory
        tool_name: Name of the tool to execute
        params: Parameters to pass to the tool

    Returns:
        Tool execution result
    """
    original_cwd = os.getcwd()
    try:
        # Change to workspace directory for tool execution
        if workspace_path:
            os.chdir(workspace_path)

        from src.tools import execute_action

        return execute_action(tool_name, params)
    finally:
        os.chdir(original_cwd)
