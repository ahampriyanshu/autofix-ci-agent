from pathlib import Path
import json
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
        try:
            with open(self.prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

            full_prompt = f"""{system_prompt}
            CURRENT OBSERVATION: {observation}
            """

            response = self.llm.invoke(full_prompt)

            try:
                reasoning_data = json.loads(response.content.strip())
                if (
                    isinstance(reasoning_data, dict)
                    and "reasoning" in reasoning_data
                    and "tool_call" in reasoning_data
                ):
                    return reasoning_data
                else:
                    return {"error": "Invalid reasoning format from LLM"}
            except json.JSONDecodeError:
                return {
                    "error": f"Failed to parse LLM response as JSON: {response.content[:100]}..."
                }

        except Exception as e:
            return {"error": f"Reasoning failed: {str(e)}"}

    def act(self, reasoning):
        try:
            if "error" in reasoning:
                return {
                    "status": "error",
                    "error": reasoning["error"],
                    "action": "none",
                    "input": "",
                }

            tool_call = reasoning.get("tool_call", {})
            tool_name = tool_call.get("tool", "")
            tool_input = tool_call.get("input", "")

            if not tool_name:
                return {
                    "status": "error",
                    "error": "No tool specified in reasoning",
                    "action": "none",
                    "input": "",
                }

            workspace_path = self.workspace_path
            if workspace_path:
                workspace_path = str(Path(workspace_path).resolve())
            else:
                return {
                    "status": "error",
                    "error": "Workspace path not set",
                    "action": tool_name,
                    "input": tool_input,
                }

            if not os.path.exists(workspace_path):
                return {
                    "status": "error",
                    "error": f"Workspace path does not exist: {workspace_path}",
                    "action": tool_name,
                    "input": tool_input,
                }

            result = execute_tool_in_workspace(workspace_path, tool_name, tool_input)

            return {
                "status": "success",
                "action": tool_name,
                "input": tool_input,
                "result": result,
            }

        except Exception as e:
            import traceback

            return {
                "status": "error",
                "error": f"Action execution failed: {str(e)}\n{traceback.format_exc()}",
                "action": tool_name if "tool_name" in locals() else "unknown",
                "input": tool_input if "tool_input" in locals() else "",
            }

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
