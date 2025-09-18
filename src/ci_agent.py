"""CI AutoFix Agent - USER IMPLEMENTS THIS FILE"""

from pathlib import Path
from .helpers import execute_tool_in_workspace

class ReActAgent:
    def __init__(self, tools, llm):
        self.tools = tools  # Pre-built tools provided
        self.llm = llm
        self.workspace_path = None
        
    def reason(self, observation):
        """
        USER IMPLEMENTS: LLM reasoning step
        
        Args:
            observation: Current state/results from previous action
            
        Returns:
            dict: {"reasoning": str, "tool_call": {"tool": str, "input": str}}
        """
        try:
            # Load the agent prompt
            import os
            prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'ci_agent_prompt.txt')
            with open(prompt_path, 'r') as f:
                system_prompt = f.read()
            
            # Create the full prompt with current observation
            full_prompt = f"""{system_prompt}

CURRENT OBSERVATION: {observation}

Based on the current observation, provide your reasoning and next tool call in JSON format:"""
            
            # Get LLM response
            response = self.llm.invoke(full_prompt)
            
            # Parse JSON response
            import json
            try:
                reasoning_data = json.loads(response.content.strip())
                if isinstance(reasoning_data, dict) and "reasoning" in reasoning_data and "tool_call" in reasoning_data:
                    return reasoning_data
                else:
                    return {"error": "Invalid reasoning format from LLM"}
            except json.JSONDecodeError:
                return {"error": f"Failed to parse LLM response as JSON: {response.content[:100]}..."}
                
        except Exception as e:
            return {"error": f"Reasoning failed: {str(e)}"}
    
    def act(self, reasoning):
        """
        USER IMPLEMENTS: Tool selection & execution
        
        Args:
            reasoning: Output from reason() step (JSON dict)
            
        Returns:
            dict: {"action": str, "input": str, "result": dict, "status": "success|error"}
        """
        try:
            if "error" in reasoning:
                return {"status": "error", "error": reasoning["error"]}
            
            tool_call = reasoning.get("tool_call", {})
            tool_name = tool_call.get("tool", "")
            tool_input = tool_call.get("input", "")
            
            if not tool_name:
                return {"status": "error", "error": "No tool specified in reasoning"}
            
            # Execute the chosen tool
            result = execute_tool_in_workspace(self.workspace_path, tool_name, tool_input)
            
            return {
                "status": "success",
                "action": tool_name,
                "input": tool_input,
                "result": result
            }
                
        except Exception as e:
            return {"status": "error", "error": f"Action execution failed: {str(e)}"}
    
    def observe(self, action_result):
        """
        USER IMPLEMENTS: Result interpretation
        
        Args:
            action_result: Output from act() step (JSON dict)
            
        Returns:
            dict: {"observation": str, "ci_status": "pass|fail|unknown", "next_action_needed": bool}
        """
        try:
            if action_result.get("status") == "error":
                return {
                    "observation": f"Error occurred: {action_result.get('error', 'Unknown error')}",
                    "ci_status": "unknown",
                    "next_action_needed": True
                }
            
            action = action_result.get("action", "unknown")
            result = action_result.get("result", {})
            
            # Handle structured tool responses
            if isinstance(result, dict) and "status" in result:
                if result["status"] == "pass":
                    if result.get("action") == "run_ci_pipeline":
                        return {
                            "observation": "CI pipeline passed - all checks successful!",
                            "ci_status": "pass",
                            "next_action_needed": False
                        }
                    elif result.get("data", {}).get("content"):
                        content = result["data"]["content"][:200] + "..." if len(result["data"]["content"]) > 200 else result["data"]["content"]
                        return {
                            "observation": f"File analysis complete: {content}",
                            "ci_status": "unknown",
                            "next_action_needed": True
                        }
                    elif result.get("data", {}).get("output"):
                        output = result["data"]["output"][:200] + "..." if len(result["data"]["output"]) > 200 else result["data"]["output"]
                        return {
                            "observation": f"Test analysis: {output}",
                            "ci_status": "unknown", 
                            "next_action_needed": True
                        }
                    else:
                        return {
                            "observation": f"{result.get('action', 'Action')} completed successfully",
                            "ci_status": "unknown",
                            "next_action_needed": True
                        }
                else:  # status == "fail"
                    error_msg = result.get("error", "Unknown error")
                    if result.get("action") == "run_ci_pipeline":
                        return {
                            "observation": f"CI pipeline failed: {error_msg}",
                            "ci_status": "fail",
                            "next_action_needed": True
                        }
                    else:
                        return {
                            "observation": f"{result.get('action', 'Action')} failed: {error_msg}",
                            "ci_status": "unknown",
                            "next_action_needed": True
                        }
            
            # Fallback for any other format
            else:
                return {
                    "observation": f"Action {action} completed with result: {str(result)[:100]}...",
                    "ci_status": "unknown",
                    "next_action_needed": True
                }
                
        except Exception as e:
            return {
                "observation": f"Observation failed: {str(e)}",
                "ci_status": "unknown", 
                "next_action_needed": True
            }
