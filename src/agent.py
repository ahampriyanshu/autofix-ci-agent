from pathlib import Path
import os
from .helpers import execute_tool_in_workspace


class ReActAgent:
    def __init__(self, tools, llm):
        self.tools = tools
        self.llm = llm
        self.workspace_path = None
        self.prompt_path = os.path.join(
            os.path.dirname(__file__), "prompts", "ci_agent_prompt.txt"
        )

    def reason(self, observation):
        """Analyze current CI state and plan next action using LLM"""
        raise NotImplementedError("reason must be implemented by the user")

    def act(self, reasoning):
        """Execute tool calls with proper error handling"""
        raise NotImplementedError("act must be implemented by the user")

    def observe(self, action_result):
        try:
            if action_result.get("status") == "error":
                return {
                    "observation": f"Error occurred: {action_result.get('error', 'Unknown error')}",
                    "ci_status": "unknown",
                    "next_action_needed": True,
                }

            action = action_result.get("action", "unknown")
            result = action_result.get("result", {})

            if isinstance(result, dict) and "status" in result:
                if result["status"] == "pass":
                    if result.get("action") == "run_ci_pipeline":
                        return {
                            "observation": "CI pipeline passed - all checks successful!",
                            "ci_status": "pass",
                            "next_action_needed": False,
                        }
                    elif result.get("data", {}).get("content"):
                        content = result["data"]["content"]
                        if len(content) > 500:
                            content = content[:500] + "..."
                        return {
                            "observation": f"File analysis complete:\n{content}",
                            "ci_status": "unknown",
                            "next_action_needed": True,
                        }
                    elif result.get("data", {}).get("output"):
                        output = (
                            result["data"]["output"][:200] + "..."
                            if len(result["data"]["output"]) > 200
                            else result["data"]["output"]
                        )
                        return {
                            "observation": f"Test analysis: {output}",
                            "ci_status": "unknown",
                            "next_action_needed": True,
                        }
                    else:
                        return {
                            "observation": f"{result.get('action', 'Action')} completed successfully. Run CI pipeline to verify the fix.",
                            "ci_status": "unknown",
                            "next_action_needed": True,
                        }
                else:
                    error_msg = result.get("error", "Unknown error")
                    if result.get("action") == "run_ci_pipeline":
                        import json
                        import re

                        observation = f"CI pipeline failed: {error_msg}"

                        try:
                            json_match = re.search(r"\{.*\}", error_msg, re.DOTALL)
                            if json_match:
                                ci_result = json.loads(json_match.group())
                                if "checks" in ci_result:
                                    failed_checks = [
                                        c
                                        for c in ci_result["checks"]
                                        if c.get("status") == "fail"
                                    ]
                                    if failed_checks:
                                        first_failure = failed_checks[0]
                                        observation = f"CI pipeline failed. First issue: {first_failure.get('test', 'unknown')} check failed. Error: {first_failure.get('error', 'No details')}"
                        except (
                            json.JSONDecodeError,
                            KeyError,
                            IndexError,
                            AttributeError,
                        ):
                            pass

                        return {
                            "observation": observation,
                            "ci_status": "fail",
                            "next_action_needed": True,
                        }
                    else:
                        return {
                            "observation": f"{result.get('action', 'Action')} failed: {error_msg}. Try a different approach or verify the file/parameters.",
                            "ci_status": "unknown",
                            "next_action_needed": True,
                        }

            else:
                return {
                    "observation": f"Action {action} completed with result: {str(result)[:100]}...",
                    "ci_status": "unknown",
                    "next_action_needed": True,
                }

        except Exception as e:
            return {
                "observation": f"Observation failed: {str(e)}",
                "ci_status": "unknown",
                "next_action_needed": True,
            }
